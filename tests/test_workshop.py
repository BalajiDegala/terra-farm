"""Regression checks for preserving learner work and rejecting unsafe AWS overrides."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkshopTests(unittest.TestCase):
    def test_linux_helper_ignores_a_windows_terraform_binary(self):
        with patch.dict(sys.modules, {'aws_local': MagicMock()}):
            helper = load('lab_platform_test', ROOT / 'scripts/lab.py')
        with tempfile.TemporaryDirectory() as temp:
            helper.ROOT = Path(temp)
            binaries = helper.ROOT / '.tools/terraform'
            binaries.mkdir(parents=True)
            (binaries / 'terraform.exe').write_bytes(b'Windows binary from another shell')
            values = {'floci_endpoint': {'value': 'http://localhost:4566'},
                      'aws_region': {'value': 'us-east-1'}}
            with patch.object(helper.os, 'name', 'posix'), \
                    patch.object(helper.shutil, 'which', return_value='/usr/bin/terraform'), \
                    patch.object(helper.subprocess, 'run') as runner:
                runner.return_value.stdout = json.dumps(values)
                helper.outputs()
                self.assertEqual(runner.call_args.args[0][0], '/usr/bin/terraform')

    def test_release_keeps_source_locks_and_excludes_learner_state(self):
        package = load('package_test', ROOT / 'scripts/package_workshop.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in package.TOP_FILES:
                (root / name).write_text('0.1.0\n' if name == 'VERSION' else 'source\n')
            for name in package.SOURCE_DIRS:
                (root / name).mkdir()
            source = root / 'examples/01'
            source.mkdir()
            (source / 'main.tf').write_text('terraform {}\n')
            (source / '.terraform.lock.hcl').write_text('# dependency checksums\n')
            (source / 'terraform.tfvars.example').write_text('project_name = "sample"\n')
            for name in ['terraform.tfstate', 'terraform.tfstate.backup', 'personal.tfvars', 'plan.tfplan']:
                (source / name).write_text('private learner data')
            (source / '.terraform').mkdir()
            (source / '.terraform/cached.tf').write_text('not source')
            (root / 'lab').mkdir()
            (root / 'lab/main.tf').write_text('learner work')
            with contextlib.redirect_stdout(io.StringIO()):
                archive = package.build_archive(root)
                first = archive.read_bytes()
                package.build_archive(root)
            self.assertEqual(archive.read_bytes(), first)
            self.assertEqual(archive.with_suffix('.zip.sha256').read_bytes(),
                             f'{hashlib.sha256(first).hexdigest()}  {archive.name}\n'.encode('utf-8'))
            with zipfile.ZipFile(archive) as download:
                names = download.namelist()
                self.assertTrue(any(name.endswith('/examples/01/.terraform.lock.hcl') for name in names))
                self.assertTrue(any(name.endswith('/examples/01/terraform.tfvars.example') for name in names))
                self.assertTrue(any(name.endswith('/MANIFEST.sha256') for name in names))
                self.assertFalse(any('/lab/' in name or '/.terraform/' in name or
                                     name.endswith(('.tfstate', '.backup', '.tfvars', '.tfplan')) for name in names))

    def test_invalid_order_never_calls_an_aws_client(self):
        sdk = MagicMock()
        with patch.dict(sys.modules, {'boto3': sdk}):
            handler = load('create_handler_test', ROOT / 'examples/07/lambda/create_order/handler.py')
        for event in [{'body': 'not JSON'}, {'product_id': 'coffee', 'quantity': True},
                      {'product_id': 'coffee', 'quantity': 0}, {'body': '[]'}]:
            self.assertEqual(handler.handler(event, None)['statusCode'], 400)
        sdk.client.assert_not_called()

    def test_processing_failure_is_returned_for_retry_without_losing_other_records(self):
        sdk = MagicMock()
        with patch.dict(sys.modules, {'boto3': sdk}):
            handler = load('process_handler_test', ROOT / 'examples/07/lambda/process_order/handler.py')
        environment = {'FLOCI_ENDPOINT': 'http://floci:4566', 'LAB_REGION': 'us-east-1',
                       'ARCHIVE_BUCKET': 'test-archive', 'ORDERS_TABLE': 'test-orders',
                       'EVENTS_TOPIC_ARN': 'arn:local:test', 'FAILURES_TOPIC_ARN': ''}
        records = [{'messageId': 'good', 'body': '{"order_id":"123"}'},
                   {'messageId': 'bad', 'body': 'not JSON'}]
        with patch.dict('os.environ', environment), patch.object(handler.logger, 'exception'):
            result = handler.handler({'Records': records}, None)
        self.assertEqual(result, {'batchItemFailures': [{'itemIdentifier': 'bad'}]})
        sdk.client.return_value.update_item.assert_called_once()

    def test_chapter_transition_keeps_state_tfvars_and_backs_up_edits(self):
        chapter = load('chapter_test', ROOT / 'scripts/chapter.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'examples/01').mkdir(parents=True)
            (root / 'examples/02').mkdir()
            (root / 'config').mkdir()
            (root / 'config/aws-local.ini').write_text('[default]\n')
            (root / 'examples/01/main.tf').write_text('first chapter')
            (root / 'examples/02/main.tf').write_text('second chapter')
            (root / 'examples/02/__pycache__').mkdir()
            (root / 'examples/02/__pycache__/junk.pyc').write_bytes(b'not course material')
            chapter.ROOT = root
            chapter.LAB = root / 'lab'
            chapter.PROGRESS = chapter.LAB / '.chapter.json'
            with patch.object(sys, 'argv', ['chapter.py', '1']), contextlib.redirect_stdout(io.StringIO()):
                chapter.main()
            state = b'{"serial": 17, "lineage": "preserve-me"}'
            (chapter.LAB / 'terraform.tfstate').write_bytes(state)
            (chapter.LAB / 'terraform.tfvars').write_text('environment = "test"')
            (chapter.LAB / 'main.tf').write_text('learner edits')
            with patch.object(sys, 'argv', ['chapter.py', '2']), contextlib.redirect_stdout(io.StringIO()):
                chapter.main()
            self.assertEqual((chapter.LAB / 'terraform.tfstate').read_bytes(), state)
            self.assertEqual((chapter.LAB / 'terraform.tfvars').read_text(), 'environment = "test"')
            self.assertEqual((chapter.LAB / 'main.tf').read_text(), 'second chapter')
            backups = list((root / '.workshop/backups').rglob('main.tf'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), 'learner edits')
            self.assertFalse((chapter.LAB / '__pycache__').exists())
            self.assertEqual(json.loads(chapter.PROGRESS.read_text())['chapter'], 2)
            with patch.object(sys, 'argv', ['chapter.py', '1']), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    chapter.main()
            self.assertEqual((chapter.LAB / 'terraform.tfstate').read_bytes(), state)

    def test_aws_wrapper_replaces_inherited_credentials_and_rejects_endpoint_override(self):
        aws = load('aws_test', ROOT / 'scripts/aws_local.py')
        with patch.dict('os.environ', {'AWS_PROFILE': 'personal', 'AWS_SESSION_TOKEN': 'personal-token',
                                       'AWS_ENDPOINT_URL_S3': 'https://example.invalid'}):
            env = aws.environment()
        self.assertEqual(env['AWS_ACCESS_KEY_ID'], 'test')
        self.assertNotIn('AWS_PROFILE', env)
        self.assertNotIn('AWS_SESSION_TOKEN', env)
        self.assertNotIn('AWS_ENDPOINT_URL_S3', env)
        with patch.object(aws.subprocess, 'run') as runner:
            for arguments in [
                    ['--endpoint-url=https://example.invalid'],
                    ['--endpoint=https://example.invalid'],
                    ['--endp', 'https://example.invalid'],
                    ['--profile=personal'], ['--prof', 'personal']]:
                with self.assertRaises(ValueError):
                    aws.run(['s3api', 'list-buckets', *arguments])
            runner.assert_not_called()
            aws.run(['s3api', 'list-buckets'])
            self.assertEqual(runner.call_args.args[0][:3], ['aws', '--endpoint-url', 'http://localhost:4566'])

    def test_missing_chapter_does_not_advance_or_modify_learner_work(self):
        chapter = load('chapter_missing_test', ROOT / 'scripts/chapter.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            chapter.ROOT = root
            chapter.LAB = root / 'lab'
            chapter.LAB.mkdir()
            chapter.PROGRESS = chapter.LAB / '.chapter.json'
            marker = '{"chapter": 6}\n'
            chapter.PROGRESS.write_text(marker)
            state = b'{"serial": 23, "lineage": "keep-me"}'
            (chapter.LAB / 'terraform.tfstate').write_bytes(state)
            with patch.object(sys, 'argv', ['chapter.py', '7']), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    chapter.main()
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(chapter.PROGRESS.read_text(), marker)
            self.assertEqual((chapter.LAB / 'terraform.tfstate').read_bytes(), state)
            # The two practice chapters deliberately have no reference directory.
            chapter.PROGRESS.write_text('{"chapter": 9}\n')
            for number in (10, 11):
                with patch.object(sys, 'argv', ['chapter.py', str(number)]), contextlib.redirect_stdout(io.StringIO()):
                    chapter.main()
                self.assertEqual(json.loads(chapter.PROGRESS.read_text())['chapter'], number)


if __name__ == '__main__':
    unittest.main()
