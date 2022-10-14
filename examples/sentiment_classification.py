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
RNN model
"""
# pylint: disable=abstract-method

import os
import shutil
import tempfile
import re
import string
import tarfile
import zipfile
import math
from typing import IO
from pathlib import Path
import requests
import six
import numpy as np
from tqdm import tqdm

import mindspore as ms
from mindspore import nn
from mindspore import ops
import mindspore.dataset as ds
from mindspore.common.initializer import Uniform, HeUniform

from mindnlp.common.metrics import Accuracy
from mindnlp.engine.trainer import Trainer
from mindnlp.abc import Seq2vecModel
from mindnlp.dataset import load
from mindnlp.modules import Glove

class Head(nn.Cell):
    """
    Head for Sentiment Classification model
    """
    def __init__(self, hidden_dim, output_dim):
        super().__init__()
        weight_init = HeUniform(math.sqrt(5))
        bias_init = Uniform(1 / math.sqrt(hidden_dim * 2))
        self.fc = nn.Dense(hidden_dim * 2, output_dim, weight_init=weight_init, bias_init=bias_init)
        self.sigmoid = nn.Sigmoid()

    def construct(self, context):
        context = ops.concat((context[-2, :, :], context[-1, :, :]), axis=1)
        output = self.fc(context)
        return self.sigmoid(output)


class SentimentClassification(Seq2vecModel):
    """
    Sentiment Classification model
    """
    def __init__(self, encoder, head, dropout):
        super().__init__(encoder, head, dropout)
        self.encoder = encoder
        self.head = head
        self.dropout = nn.Dropout(1 - dropout)

    def construct(self, src_tokens, mask=None):
        _, (hidden, _), _ = self.encoder(src_tokens)
        hidden = self.dropout(hidden)
        output = self.head(hidden)
        return output

# load datasets
imdb_train, imdb_test = load('imdb')
embedding, vocab = Glove.from_pretrained('6B', 100)

lookup_op = ds.text.Lookup(vocab, unknown_token='<unk>')
pad_op = ds.transforms.PadEnd([500], pad_value=vocab.tokens_to_ids('<pad>'))
type_cast_op = ds.transforms.TypeCast(ms.float32)

imdb_train = imdb_train.map(operations=[lookup_op, pad_op], input_columns=['src_tokens'])
imdb_train = imdb_train.map(operations=[type_cast_op], input_columns=['label'])

imdb_test = imdb_test.map(operations=[lookup_op, pad_op], input_columns=['src_tokens'])
imdb_test = imdb_test.map(operations=[type_cast_op], input_columns=['label'])

imdb_train, imdb_valid = imdb_train.split([0.7, 0.3])

# define Models & Loss & Optimizer
hidden_size = 256
output_size = 1
num_layers = 2
bidirectional = True
drop = 0.5
lr = 0.001

# sentiment_encoder = LSTMEncoder(vocab_size, embedding_dim, hidden_size, num_layers=num_layers,
#                                 dropout=drop, bidirectional=bidirectional)
# sentiment_head = Head(hidden_size, output_size)
# net = SentimentClassification(sentiment_encoder, sentiment_head, drop)

# loss = nn.BCELoss(reduction='mean')
# optimizer = nn.Adam(net.trainable_params(), learning_rate=lr)

# # define metrics
# metric = Accuracy()

# # define trainer

# trainer = Trainer(network=net, train_dataset=imdb_train, eval_dataset=imdb_valid, metrics=metric,
#                   epochs=2, batch_size=64, loss_fn=loss, optimizer=optimizer)
# trainer.run(tgt_columns="label")
# print("end train")