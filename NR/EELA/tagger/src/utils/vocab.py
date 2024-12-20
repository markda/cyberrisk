# -*- coding: utf-8 -*-

from collections import Counter

import regex
import torch
import time

class Vocab(object):
    PAD = '<PAD>'
    UNK = '<UNK>'
    EOS = '<EOS>'

    def __init__(self, words, chars, flags, tags):
        self.pad_index = 0
        self.unk_index = 1
        self.words = [self.PAD, self.UNK] + sorted(words)
        self.words = [self.PAD, self.UNK] + sorted(words)
        '''self.tags =  ["probably_not_exploited",
                      "unlikely_to_be_exploited",
                      "unclear",
                      "could_be_exploited",
                      "probably_exploited"] 
        '''
        self.tags =  ["unlikely_to_be_exploited",
                      "unclear",
                      "could_be_exploited"]
                      
        self.chars = [self.PAD, self.UNK] + sorted(chars)
        self.cve_flags = [self.PAD, "cve"]
        self.word_dict = {word: i for i, word in enumerate(self.words)}
        self.tag_dict = {tag: i for i, tag in enumerate(self.tags)}
        self.char_dict = {char: i for i, char in enumerate(self.chars)}
        self.cve_flag_dict = {flag: i for i, flag in enumerate(self.cve_flags)}

        # ids of punctuation that appear in words
        self.puncts = sorted(i for word, i in self.word_dict.items()
                             if regex.match(r'\p{P}+$', word))

        self.n_words = len(self.words)
        self.n_tags = len(self.tags)
        self.n_chars = len(self.chars)
        self.n_train_words = self.n_words

    def __repr__(self):
        info = f"{self.__class__.__name__}: "
        info += f"{self.n_words} words, "
        info += f"{self.n_chars} chars, "
        info += f"{self.n_tags} tags"
        return info

    def word2id(self, sequence):
        return torch.tensor([self.word_dict.get(word.lower(), self.unk_index)
                             for word in sequence])

    def tag2id(self, sequence):
        return torch.tensor([self.tag_dict.get(tag, self.tag_dict["unclear"])
                             for tag in sequence])

    def flag2id(self, sequence):
        return torch.tensor([self.cve_flag_dict.get(flag, self.pad_index)
                             for flag in sequence])
    
    def char2id(self, sequence, max_length=20):
        char_ids = torch.zeros(len(sequence), max_length, dtype=torch.long)
        for i, word in enumerate(sequence):
            ids = torch.tensor([self.char_dict.get(c, self.unk_index)
                                for c in word[:max_length]])
            char_ids[i, :len(ids)] = ids

        return char_ids

    def id2tag(self, ids):
        return [self.tags[i] for i in ids]
    
    def read_embeddings(self, embed, smooth=True):
        # if the UNK token has existed in the pretrained,
        # then use it to replace the one in the vocab
        if embed.unk:
            self.UNK = embed.unk
        
        self.extend(embed.tokens)
        self.embeddings = torch.rand(self.n_words, embed.dim)
        for i, word in enumerate(self.words):
            if word in embed:
                self.embeddings[i] = embed[word]
                            
        if smooth:
            self.embeddings /= torch.std(self.embeddings)
        
    def randomly_initialise_embeddings(self, n_dim, smooth=True):
        self.embeddings = torch.randn(self.n_words, n_dim)
        if smooth:
            self.embeddings /= torch.std(self.embeddings)

    def extend(self, words):
        self.words += sorted(set(words).difference(self.word_dict))
        self.chars += sorted(set(''.join(words)).difference(self.char_dict))
        self.word_dict = {w: i for i, w in enumerate(self.words)}
        self.char_dict = {c: i for i, c in enumerate(self.chars)}
        self.puncts = sorted(i for word, i in self.word_dict.items()
                             if regex.match(r'\p{P}+$', word))
        self.n_words = len(self.words)
        self.n_chars = len(self.chars)

    def numericalize(self, corpus, training=True):
        st = time.time()
        words = [self.word2id(seq) for seq in corpus.words]
        tags = [self.tag2id(seq) for seq in corpus.tags]
        chars = [self.char2id(seq) for seq in corpus.words]
        flags = [self.flag2id(seq) for seq in corpus.flags]
        if not training:
            return words, chars, flags
        print(len(words)/(time.time()-st))
        return words, chars, flags, tags

    @classmethod
    def from_corpus(cls, corpus, min_freq=2):
        words = []
        chars = []
        tags = []
        words = Counter(word.lower() for seq in corpus.words for word in seq)
        words = list(word for word, freq in words.items() if freq >= min_freq)
        chars = list({char for seq in corpus.words for char in ''.join(seq)})
        tags = list({tag for seq in corpus.tags for tag in seq})
        flags = list({flag for seq in corpus.flags for flag in seq})
        
        vocab = cls(words, chars, flags, tags)
        return vocab
