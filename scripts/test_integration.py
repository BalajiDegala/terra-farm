"""Maintainer check: provision, exercise, and destroy a uniquely named LOCAL Floci lab."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import aws_local
from check_workshop import (ROOT, copy_chapter, import_example, initialize,
                            isolated_workspace, remove_workspace, run, terraform_binary)


class CourseRun:
    def __init__(self, terraform, plugin_dir=None):
        self.terraform = terraform
        self.plugin_dir = plugin_dir
        self.work = isolated_workspace("integration-")
        self.lab = self.work / "lab"
        self.project = "workshop-ci-" + uuid.uuid4().hex[:8]
        self.prefix = self.project + "-dev"
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("TF_")}
        self.env["PATH"] = str(Path(terraform).parent) + os.pathsep + self.env.get("PATH", "")
        self.env["PYTHONIOENCODING"] = "utf-8"
        print(f"Isolated project: {self.project}; preserved on failure: {self.work}", flush=True)

    def tf(self, *args, cwd=None, **kwargs):
        return run([self.terraform, *args], cwd=cwd or self.lab, env=self.env, **kwargs)

    def init(self, directory):
        initialize(self.terraform, directory, self.plugin_dir, self.env, backend=True)

    def helper(self, action):
        output = run([sys.executable, self.work / "scripts/lab.py", action], cwd=self.lab,
                     env=self.env, timeout=300)
        if action == "publish" and '"lesson": "messaging"' not in output:
            raise RuntimeError("SNS publish did not produce the expected notification queue message")
        print(output, end="", flush=True)

    def state(self, directory=None):
        return {line for line in self.tf("state", "list", cwd=directory).splitlines()
                if not line.startswith("data.") and ".data." not in line}

    def clean_plan(self, directory=None):
        self.tf("plan", "-input=false", "-no-color", "-detailed-exitcode", cwd=directory)

    def plan(self, name, *options, directory=None):
        directory = directory or self.lab
        file = directory / f"{name}.tfplan"
        self.tf("plan", "-input=false", "-no-color", f"-out={file.as_posix()}", *options, cwd=directory)
        data = json.loads(self.tf("show", "-json", file, cwd=directory))
        changes = {item["address"]: item["change"]["actions"]
                   for item in data.get("resource_changes", [])
                   if item["mode"] == "managed" and item["change"]["actions"] != ["no-op"]}
        print(f"Reviewed plan {name}: {json.dumps(changes, sort_keys=True)}", flush=True)
        return file, data, changes

    def apply(self, file, directory=None):
        self.tf("apply", "-input=false", "-no-color", file, cwd=directory)

    def exercise(self, name, options=(), expected=None):
        file, data, changes = self.plan(name, *options)
        if expected is not None and changes != expected:
            raise RuntimeError(f"Unexpected {name} plan: {changes}; expected {expected}")
        self.apply(file)
        self.clean_plan()
        return data

    def chapters(self):
        totals = {1: 0, 2: 4, 3: 6, 4: 13, 5: 21, 6: 24, 7: 29, 8: 33, 9: 36}
        for number, total in totals.items():
            copy_chapter(self.work, number)
            if number == 1:
                (self.lab / "terraform.tfvars").write_text(f'project_name = "{self.project}"\n', encoding="utf-8")
            if number in (1, 3, 7):
                self.init(self.lab)
            self.tf("validate", "-no-color")
            file, _, changes = self.plan(f"chapter{number:02d}")
            if any("delete" in actions and address != "local_file.app_config"
                   for address, actions in changes.items()):
                raise RuntimeError("A chapter proposed unexpected infrastructure deletion")
            self.apply(file)
            self.clean_plan()
            if len(self.state()) != total:
                raise RuntimeError(f"Chapter {number}: expected {total} managed resources")
            if number == 4:
                self.helper("publish")
            elif number == 7:
                self.helper("smoke-lambda")
            elif number == 8:
                self.helper("smoke-api")
            elif number == 9:
                self.helper("event")
            print(f"PASS: Chapter {number:02d}, {total} resources, converged", flush=True)

        copy_chapter(self.work, 10)
        if self.prefix not in self.tf("console", input="local.name_prefix\n"):
            raise RuntimeError("Unexpected console result")
        if "digraph" not in self.tf("graph"):
            raise RuntimeError("Terraform graph is missing")
        print("PASS: console and graph", flush=True)
        copy_chapter(self.work, 11)
        self.helper("drift")
        self.exercise("drift", expected={"aws_sqs_queue.orders": ["update"]})
        self.helper("import-create")
        (self.lab / "imported.tf").write_text(import_example(), encoding="utf-8")
        self.tf("import", "-input=false", "-no-color", "aws_ssm_parameter.imported_note", f"/{self.prefix}/imported-note")
        file, _, changes = self.plan("import")
        if changes not in ({}, {"aws_ssm_parameter.imported_note": ["update"]}):
            raise RuntimeError(f"Unexpected import plan: {changes}")
        self.apply(file)
        self.clean_plan()
        self.exercise("replace", ["-replace=local_file.app_config"],
                      {"local_file.app_config": ["delete", "create"]})
        print("PASS: drift, import, replacement", flush=True)
        copy_chapter(self.work, 12)
        self.init(self.lab)
        data = self.exercise("modules", expected={})
        moves = {item["previous_address"] for item in data["resource_changes"] if "previous_address" in item}
        if moves != {"aws_s3_bucket.assets", "aws_s3_bucket.order_archive"}:
            raise RuntimeError(f"Unexpected module moves: {moves}")
        self.helper("smoke-api")
        print("PASS: module refactor preserves resources and order flow", flush=True)

    def backend(self):
        self.bootstrap = self.work / "state-bootstrap"
        shutil.copytree(self.work / "examples/13-bootstrap", self.bootstrap)
        self.bucket = self.project + "-state"
        main = self.bootstrap / "main.tf"
        main.write_text(main.read_text(encoding="utf-8").replace('"terraform-workshop-state"', json.dumps(self.bucket)), encoding="utf-8")
        self.init(self.bootstrap)
        file, _, changes = self.plan("bootstrap", directory=self.bootstrap)
        if changes != {"aws_s3_bucket.state": ["create"], "aws_s3_bucket_versioning.state": ["create"]}:
            raise RuntimeError("Unexpected bootstrap plan")
        self.apply(file, self.bootstrap)
        before = self.state()
        backend = (self.work / "examples/13-backend/backend.tf").read_text(encoding="utf-8")
        (self.lab / "backend.tf").write_text(backend.replace('"terraform-workshop-state"', json.dumps(self.bucket)), encoding="utf-8")
        self.tf("init", "-migrate-state", "-no-color", input="yes\n")
        if self.state() != before:
            raise RuntimeError("Remote migration changed state addresses")
        self.clean_plan()
        self.check_lock()
        (self.lab / "backend.tf").rename(self.lab / "backend.tf.disabled")
        self.tf("init", "-migrate-state", "-no-color", input="yes\n")
        if self.state() != before:
            raise RuntimeError("Local migration changed state addresses")
        self.clean_plan()
        print("PASS: backend round trip and lock contention", flush=True)

    def check_lock(self):
        log_path = self.work / "lock-test.log"
        with log_path.open("w", encoding="utf-8") as log:
            holder = subprocess.Popen([self.terraform, "apply", "-no-color", "-var=demo_secret_note=lock-demo"],
                                      cwd=self.lab, env=self.env, stdin=subprocess.PIPE, stdout=log,
                                      stderr=subprocess.STDOUT, text=True, encoding="utf-8")
            try:
                deadline = time.monotonic() + 120
                while "Enter a value:" not in log_path.read_text(encoding="utf-8"):
                    if holder.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("Lock-holder did not reach approval prompt")
                    time.sleep(0.5)
                result = subprocess.run([self.terraform, "plan", "-input=false", "-no-color", "-lock-timeout=5s"],
                                        cwd=self.lab, env=self.env, capture_output=True, text=True,
                                        encoding="utf-8", timeout=60)
                if result.returncode != 1 or "Error acquiring the state lock" not in result.stdout + result.stderr:
                    raise RuntimeError("Second operation did not report lock contention")
            finally:
                holder.communicate("no\n", timeout=60)
        self.clean_plan()

    def destroy(self, directory, name, expected_count):
        file, data, changes = self.plan(name, "-destroy", directory=directory)
        if len(changes) != expected_count or set(changes) != self.state(directory):
            raise RuntimeError("Destroy plan does not match the isolated managed state")
        if any(actions != ["delete"] for actions in changes.values()):
            raise RuntimeError("Destroy plan contains a non-delete operation")
        for item in data.get("resource_changes", []):
            if item["address"] in changes:
                before = item["change"]["before"]
                print(f"  delete {item['address']}: {before.get('id', '(local resource)')}", flush=True)
        if directory == self.lab:
            # Known Floci workaround: remove only this run's disposable archive objects.
            archive = self.prefix + "-archive"
            output = json.loads(self.tf("output", "-json", "archive_bucket"))
            if output != archive:
                raise RuntimeError("Archive bucket does not match this isolated run")
            aws_local.run(["s3", "rm", f"s3://{archive}", "--recursive"], capture=True)
        self.apply(file, directory)
        if self.state(directory):
            raise RuntimeError("Resources remain in state after cleanup")
        print(f"PASS: destroyed {expected_count} managed resources", flush=True)

    def execute(self):
        self.chapters()
        self.backend()
        self.destroy(self.lab, "destroy-app", 37)
        self.destroy(self.bootstrap, "destroy-backend", 2)
        self.verify_cleanup()
        remove_workspace(self.work)
        print("PASS: complete integration course and cleanup", flush=True)

    def verify_cleanup(self):
        for service, operation in [
                ("s3api", "list-buckets"), ("dynamodb", "list-tables"), ("sqs", "list-queues"),
                ("sns", "list-topics"), ("lambda", "list-functions"), ("iam", "list-roles"),
                ("ssm", "describe-parameters"), ("secretsmanager", "list-secrets"),
                ("logs", "describe-log-groups"), ("apigateway", "get-rest-apis"),
                ("events", "list-event-buses"), ("kms", "list-aliases")]:
            result = aws_local.run([service, operation], capture=True).stdout
            if self.project in result:
                raise RuntimeError(f"Test-prefixed entries remain in {service} {operation}")
        print("PASS: no test-prefixed service entries remain (KMS deletion can be pending)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Create and destroy isolated local test resources")
    parser.add_argument("--terraform")
    parser.add_argument("--plugin-dir")
    args = parser.parse_args()
    if not args.run:
        parser.error("Read runbooks/maintaining.md, start Floci, then pass --run to exercise local infrastructure.")
    identity = json.loads(aws_local.run(["sts", "get-caller-identity"], capture=True).stdout)
    if identity.get("Account") != "000000000000":
        raise RuntimeError("Expected the local Floci account")
    course = CourseRun(terraform_binary(args.terraform), args.plugin_dir)
    try:
        course.execute()
    except BaseException:
        print(f"FAILED. Keep Floci running. Test source/state retained at {course.work}; follow Chapter 14 to clean up.", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
