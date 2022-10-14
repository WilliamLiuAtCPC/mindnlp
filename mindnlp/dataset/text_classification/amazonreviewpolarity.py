# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""
AmazonReviewPolarity dataset
"""
# pylint: disable=C0103

import os
import csv
from typing import Union, Tuple
from mindspore.dataset import GeneratorDataset, text
from mindspore.dataset.text import BasicTokenizer
from mindnlp.utils.download import cache_file
from mindnlp.dataset.register import load, process
from mindnlp.configs import DEFAULT_ROOT
from mindnlp.utils import untar

URL = "https://drive.google.com/uc?export=download&id=0Bz8a_Dbh9QhbaW12WVVZS2drcnM&confirm=t"

MD5 = "fe39f8b653cada45afd5792e0f0e8f9b"


class Amazonreviewpolarity:
    """
    AmazonReviewPolarity dataset source
    """

    def __init__(self, path) -> None:
        self.path: str = path
        self._label, self._title_text = [], []
        self._load()

    def _load(self):
        csvfile = open(self.path, "r", encoding="utf-8")
        dict_reader = csv.reader(csvfile)
        for row in dict_reader:
            self._label.append(int(row[0]))
            self._title_text.append(f"{row[1]} {row[2]}")

    def __getitem__(self, index):
        return self._label[index], self._title_text[index]

    def __len__(self):
        return len(self._label)


@load.register
def AmazonReviewPolarity(
    root: str = DEFAULT_ROOT,
    split: Union[Tuple[str], str] = ("train", "test"),
    proxies=None,
):
    r"""
    Load the AmazonReviewPolarity dataset
    Args:
        root (str): Directory where the datasets are saved.
            Default:~/.mindnlp
        split (str|Tuple[str]): Split or splits to be returned.
            Default:('train', 'test').

    Returns:
        - **datasets_list** (list) -A list of loaded datasets.
            If only one type of dataset is specified,such as 'trian',
            this dataset is returned instead of a list of datasets.

    Examples:
        >>> dataset_train,dataset_test = AmazonReviewPolarity()
        >>> train_iter = dataset_train.create_tuple_iterator()
        >>> print(next(train_iter))

    """

    cache_dir = os.path.join(root, "datasets", "AmazonReviewPolarity")
    path_dict = {
        "train": "train.csv",
        "test": "test.csv",
    }
    column_names = ["label", "title_text"]
    path_list = []
    datasets_list = []
    path, _ = cache_file(
        None,
        cache_dir=cache_dir,
        url=URL,
        md5sum=MD5,
        download_file_name="amazon_review_polarity_csv.tar.gz",
        proxies=proxies,
    )

    untar(path, cache_dir)
    if isinstance(split, str):
        path_list.append(os.path.join(cache_dir, "amazon_review_polarity_csv", path_dict[split]))
    else:
        for s in split:
            path_list.append(os.path.join(cache_dir, "amazon_review_polarity_csv", path_dict[s]))
    for path in path_list:
        datasets_list.append(
            GeneratorDataset(
                source=Amazonreviewpolarity(path), column_names=column_names, shuffle=False
            )
        )
    if len(path_list) == 1:
        return datasets_list[0]
    return datasets_list

@process.register
def AmazonReviewPolarity_Process(dataset, column="title_text", tokenizer=BasicTokenizer(), vocab=None):
    """
    the process of the AmazonReviewPolarity dataset

    Args:
        dataset (GeneratorDataset): AmazonReviewPolarity dataset.
        column (str): the column needed to be transpormed of the AmazonReviewPolarity dataset.
        tokenizer (TextTensorOperation): tokenizer you choose to tokenize the text dataset.
        vocab (Vocab): vocabulary object, used to store the mapping of token and index.

    Returns:
        - **dataset** (MapDataset) - dataset after transforms.
        - **Vocab** (Vocab) - vocab created from dataset

    Raises:
        TypeError: If `input_column` is not a string.

    Examples:
        >>>from mindnlp.dataset.amazonreviewpolarity import AmazonReviewPolarity
        >>>train_dataset, test_dataset = AmazonReviewPolarity()
        >>>column = "title_text"
        >>>tokenizer = BasicTokenizer()
        >>>amazonreviewpolarity_dataset, vocab = AmazonReviewPolarity_Process(train_dataset, column, tokenizer)
        >>>amazonreviewpolarity_dataset = amazonreviewpolarity_dataset.create_tuple_iterator()
        >>>print(next(amazonreviewpolarity_dataset))

    """

    if vocab is None:
        dataset = dataset.map(tokenizer,  input_columns=column)
        vocab = text.Vocab.from_dataset(dataset, columns=column)
        return dataset.map(text.Lookup(vocab), input_columns=column), vocab
    dataset = dataset.map(tokenizer,  input_columns=column)
    return dataset.map(text.Lookup(vocab), input_columns=column)