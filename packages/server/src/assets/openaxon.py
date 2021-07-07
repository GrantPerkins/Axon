import json
import os
import sys
from glob import glob
from shutil import copyfile, rmtree
from zipfile import ZipFile

import pandas
from PIL import Image

from download import download_dataset
from progress import Progress


class OpenImagesDownloader:
    """
    Class for converting OpenImages format into an Axon usable format (TFRecords)
    """

    def __init__(self, create_id):
        """
        Set up attributes, parse JSON
        :param data_json:
        """
        self.create_id = create_id
        data_json = "/tmp/{}/data.json".format(self.create_id)
        try:
            assert os.path.isfile(data_json)
        except AssertionError:
            print("Not Found:", data_json)
            sys.exit(1)
        with open(data_json) as file:
            self.data = json.load(file)
        # will error if not in Title Case
        self.labels = [i.title() for i in self.data["labels"]]
        self.title = "_".join([i.replace(" ", "") for i in self.labels])
        self.name = "{}/OpenImages_{}.zip".format(sys.argv[1], self.title)
        assert type(self.labels) == list
        self.limit = self.data["limit"]
        assert type(self.limit) == int
        print("Hyperparameters", self.data)
        self.directory = "/tmp/{}".format(create_id)
        print("Getting dataset, size: {}, contents: {}".format(self.limit, self.labels))
        self.label_map = {}
        self.image_data = {}
        self.csv = []
        self.progress = Progress(os.path.join(self.directory, "progress.json"))

    def download(self):
        """
        API call to download OpenImages slice
        :return: None
        """
        download_dataset(dest_dir=self.directory + "/train", meta_dir="./data/create", class_labels=self.labels,
                         exclusions_path=None, limit=self.limit, progress=self.progress)

    def parse_line(self, key, label, height, width, box):
        """
        Add a line to the csv
        :param key:
        :param label:
        :param height:
        :param width:
        :param box:
        :return:
        """
        self.csv.append({
            "filename": key,
            "height": height,
            "width": width,
            "class": label,
            "xmin": int(box["xmin"] * width),
            "xmax": int(box["xmax"] * width),
            "ymin": int(box["ymin"] * height),
            "ymax": int(box["ymax"] * height)
        })

    def create_csv(self):
        print("Parsing huge .csv. Give me a minute.")
        images = glob(self.directory + "/train/*/images/*.jpg")
        with open(os.path.join("./data/create/class-descriptions-boxable.csv")) as file:
            for row in file.readlines():
                row = row.rstrip().split(',')
                self.label_map.update({row[0]: row[1]})

        for sub_dir in ["tar", "tar/train", "tar/test"]:
            sub_dir = self.directory + "/" + sub_dir
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)

        for image_path in images:
            im = Image.open(image_path)
            width, height = im.size
            file_id = image_path.split("/")[-1].rstrip(".jpg")
            copyfile(image_path, self.directory + "/tar/" + image_path.split("/")[-1])
            self.image_data.update({file_id: {"height": height, "width": width}})

        all_labels_df = pandas.read_csv(os.path.join("./data/create/train-annotations-bbox.csv"))
        all_labels_df.set_index("ImageID", inplace=True)

        labels = [i.lower() for i in self.labels]
        for key in self.image_data.keys():
            entry = all_labels_df.loc[key]
            try:
                height = self.image_data[key]["height"]
                width = self.image_data[key]["width"]
                if type(entry) == pandas.DataFrame:
                    for row in entry.iterrows():
                        box = {i.lower(): row[1][i] for i in ["XMin", "XMax", "YMin", "YMax"]}
                        label = self.label_map[row[1]["LabelName"]].lower()
                        if label in labels:
                            self.parse_line(key + '.jpg', label, height, width, box)
                else:
                    box = {i.lower(): entry.get(i) for i in ["XMin", "XMax", "YMin", "YMax"]}
                    label = self.label_map[entry.get("LabelName")].lower()
                    if label in labels:
                        self.parse_line(key + '.jpg', label, height, width, box)
            except KeyError:
                pass

        self.progress.update(3 / 8)

        print("creating subfolders")
        self.create_subfolders("train")
        self.progress.update(4 / 8)
        self.create_subfolders("test")
        self.progress.update(5 / 8)

    def create_subfolders(self, name):
        with open(self.directory + f"/tar/{name}/_annotations.csv", 'w+') as csv:
            csv.write("filename,width,height,class,xmin,ymin,xmax,ymax\n")

            csv_len = len(self.csv)
            if name == "train":
                split = range(int(csv_len * .7))
            else:
                split = range(int(csv_len * .7), csv_len)

            for i in split:
                row = self.csv[i]
                csv.write("{},{},{},{},{},{},{},{}\n".format(row["filename"], row["width"], row["height"], row["class"],
                                                             row["xmin"], row["ymin"], row["xmax"], row["ymax"]))
                copyfile(self.directory + "/tar/" + row["filename"],
                         self.directory + "/tar/" + name + '/' + row["filename"])

    def make_zip(self):
        with ZipFile("data/datasets/{}".format(self.name), 'w') as zipFile:
            for directory in "train test".split():
                for folderName, subfolders, filenames in os.walk(self.directory + "/tar/" + directory):
                    for filename in filenames:
                        # create complete filepath of file in directory
                        file = os.path.join(directory, filename)
                        # Add file to zip
                        zipFile.write(self.directory + "/tar/" + directory + '/' + filename, file)

    def make_json(self):
        with open("data/create/output.json", 'w+') as f:
            f.write('{' + '"{}": "{}"'.format(self.create_id, self.name) + '}\n')

    def clean(self):
        rmtree(self.directory)
        print("Cleaned", self.directory)


if __name__ == "__main__":
    print("Python initialized")
    downloader = OpenImagesDownloader(sys.argv[1])
    downloader.download()
    downloader.create_csv()
    print("Making archive")
    downloader.make_zip()
    downloader.progress.update(6 / 8)
    downloader.make_json()
    downloader.progress.update(7 / 8)
    downloader.clean()
    downloader.progress.update(8 / 8)
    print("Clean up done.")
