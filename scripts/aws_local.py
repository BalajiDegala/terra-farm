"""Run AWS CLI with fake credentials and an explicit localhost endpoint on any OS."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "http://localhost:4566"


def environment():
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("AWS_"):
            del env[name]
    env.update(AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
               AWS_CONFIG_FILE=str(ROOT / "config" / "aws-local.ini"),
               AWS_SHARED_CREDENTIALS_FILE=str(ROOT / "config" / "aws-local.ini"),
               AWS_DEFAULT_REGION="us-east-1", AWS_REGION="us-east-1",
               AWS_EC2_METADATA_DISABLED="true", AWS_PAGER="", AWS_CLI_AUTO_PROMPT="off")
    return env


def run(arguments, capture=False):
    # AWS CLI also accepts abbreviated global flags, such as --endpoint and --prof.
    # Block those forms before invoking it, including both --flag=value and --flag value.
    for argument in arguments:
        option = argument.split("=", 1)[0]
        if len(option) > 2 and option.startswith("--") and any(
                protected.startswith(option) for protected in ("--endpoint-url", "--profile")):
            raise ValueError("This helper always uses the repository's local Floci endpoint and fake credentials.")
    return subprocess.run(["aws", "--endpoint-url", ENDPOINT, "--region", "us-east-1",
                           "--no-cli-pager", "--output", "json", "--cli-connect-timeout", "5",
                           "--cli-read-timeout", "60", *arguments], env=environment(),
                          check=True, capture_output=capture, text=True, encoding="utf-8")


if __name__ == "__main__":
    try:
        run(sys.argv[1:])
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
