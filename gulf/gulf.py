import json
import os
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


class Gulf():
    config_filename = "gulf.json"
    archive_filename = "gulf.zip"

    def run(self):
        self.configure()
        archive_path = self.deflate()
        self.upload(archive_path)
        self.inflate()

    def configure(self):
        if not os.path.exists(self.config_filename):
            print(f"Missing {self.config_filename}")
            exit(1)
        with open(self.config_filename) as file:
            try:
                config = json.load(file)
            except json.decoder.JSONDecodeError:
                print(f"Invalid {self.config_filename}")
                exit(1)
        self.host = config.get("host", None)
        if not self.host:
            print(f"Missing host in {self.config_filename}")
            exit(1)
        self.username = config.get("username", None)
        if not self.username:
            print(f"Missing username in {self.config_filename}")
            exit(1)
        self.path = config.get("path", None)
        if not self.path:
            print(f"Missing path in {self.config_filename}")
            exit(1)
        if not self.path.endswith("/"):
            self.path += "/"
        self.password = config.get("password", None)
        if self.password and not shutil.which("sshpass"):
            print("Please install sshpass to connect using a password")
            exit(1)
        self.exclude = config.get("exclude", [])
        self.pre = config.get("pre", [])
        self.post = config.get("post", [])

    def deflate(self):
        archive_path = os.path.join(
            tempfile.gettempdir(),
            self.archive_filename
        )
        print(f"Archive:  {archive_path}")
        base_path = os.getcwd()
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(base_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, base_path)
                    if (
                        filename == self.config_filename
                        or filename == self.archive_filename
                        or filename in self.exclude
                        or relative_path in self.exclude
                        or list(filter(relative_path.startswith, self.exclude))
                    ):
                        continue
                    print(f"  deflating: {relative_path}")
                    zip.write(file_path, relative_path)
        return archive_path

    def upload(self, archive_path):
        target = "{username}@{host}:{path}".format(
            host=self.host,
            username=self.username,
            path=self.path
        )
        print(f"Copying {archive_path} to {target}")
        args = ["scp", "-v", archive_path, target]
        if self.password:
            args = ["sshpass", "-p", self.password] + args
        process = subprocess.Popen(args)
        _, code = os.waitpid(process.pid, 0)
        if code > 0:
            print("Upload failed")
            print(f"Exit code: {code}")
            exit(1)

    def inflate(self):
        machine = "{username}@{host}".format(
            host=self.host,
            username=self.username
        )
        archive_path = os.path.join(self.path, self.archive_filename)
        commands = [
            "cd {path}".format(path=os.path.dirname(archive_path)),
            *self.pre,
            "unzip -o {path}".format(path=archive_path),
            "rm {path}".format(path=archive_path),
            *self.post
        ]
        args = ["ssh", machine, " && ".join(commands)]
        if self.password:
            args = ["sshpass", "-p", self.password] + args
        process = subprocess.Popen(args)
        _, code = os.waitpid(process.pid, 0)
        if code > 0:
            print("Inflate failed")
            print(f"Exit code: {code}")
            exit(1)
