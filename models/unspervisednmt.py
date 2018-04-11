import torch
from torch import nn
from models import Transformer
import utils


def find_key_from_val(dict_, value):
    for k, v in dict_.items():
        if v == value:
            return k


def index_select_train(lang_id, input_):
    index = torch.nonzero(input_[0][:, 1] == lang_id)
    if index.numel() > 0:
        index = index[:, 0]
        x_block = torch.index_select(input_[0], 0, index)
        y_in_block = torch.index_select(input_[1], 0, index)
        y_out_block = torch.index_select(input_[2], 0, index)
        return x_block, y_in_block, y_out_block
    else:
        return None


def index_select_translate(lang_id, input_):
    index = torch.nonzero(input_[:, 1] == lang_id)
    if index.numel() > 0:
        index = index[:, 0]
        x_block = torch.index_select(input_, 0, index)
        return index, x_block
    return index, input_


class Discriminator(nn.Module):
    def __init__(self, config):
        super(Discriminator, self).__init__()
        self.config = config
        layers = [nn.Dropout(config.discriminator_dropout),
                  nn.Linear(config.hidden_size, 1024),
                  nn.LeakyReLU()]
        for _ in range(config.num_discriminator_layers - 1):
            layers.append(nn.Dropout(config.discriminator_dropout))
            layers.append(nn.Linear(1024, 1024))
            layers.append(nn.LeakyReLU())
        layers.append(nn.Dropout(config.discriminator_dropout))
        layers.append(nn.Linear(1024, 1))

    def forward(self):
        pass


                 
                 	

class UnsupervisedNMT(nn.Module):
    def __init__(self, config):
        super(UnsupervisedNMT, self).__init__()
        self.config = config
        self.model = Transformer(config)

    def forward(self, *args):
        # Identify the row indexes corresponding to lang1 and lang2
        lang1_input = index_select_train(self.lang1, args)
        if lang1_input is not None:
            loss1, stats1 = self.model1(*lang1_input)
        else:
            loss1 = 0.
            stats1 = utils.Statistics()

        lang2_input = index_select_train(self.lang2, args)
        if lang2_input is not None:
            loss2, stats2 = self.model2(*lang2_input)
        else:
            loss2 = 0.
            stats2 = utils.Statistics()

        n_total = stats1.n_words + stats2.n_words
        n_correct = stats1.n_correct + stats2.n_correct

        loss = ((loss1 * stats1.n_words) + (loss2 * stats2.n_words))/ n_total
        stats = utils.Statistics(loss=loss.data.cpu() * n_total,
                                 n_correct=n_correct,
                                 n_words=n_total)
        return loss, stats

    def translate(self, x_block, max_length=50, beam=5, alpha=0.6):
        # Identify the row indexes corresponding to lang1 and lang2
        index1, x_block1 = index_select_translate(self.lang1, x_block)
        if index1.numel() > 0:
            id_list1 = self.model1.translate(x_block1, max_length, beam, alpha)
        else:
            id_list1 = []

        index2, x_block2 = index_select_translate(self.lang2, x_block)
        if index2.numel() > 0:
            id_list2 = self.model2.translate(x_block2, max_length, beam, alpha)
        else:
            id_list2 = []

        index = index1.data.tolist() + index2.data.tolist()
        id_list = id_list1 + id_list2
        concat = list(zip(index, id_list))
        _, output = zip(*sorted(concat, key=lambda x: x[0]))
        return list(output)











