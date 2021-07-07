import json


class Progress:
    def __init__(self, path):
        self.path = path

    def update(self, progress):
        with open(self.path, 'w+') as progress_file:
            progress = {"progress": progress}
            json.dump(progress, progress_file)
