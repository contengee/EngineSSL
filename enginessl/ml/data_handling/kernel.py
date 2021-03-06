import numpy as np
import sys
import os
import gc
import inspect
import glob
import shutil
from keras.preprocessing.image import load_img, img_to_array, array_to_img, save_img , ImageDataGenerator
from keras.utils import to_categorical
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
#消したい
from common_handler.path_handler import get_path_with_glob
from tqdm import tqdm
from datetime import datetime
# Generate conflicting images fully automatically :)

# [usage]
# 2 step (Please set param.yaml in advance.)
#
# instance = OpponentImage(Kernel):
# instance.return_datafile()
#
# too easy ! :)

class Kernel():

    def __init__(self, image_tanks=[]):
        self.exec_path = os.path.dirname(os.path.abspath(__file__))
        base = 'enginessl'
        img_dir = 'data/img'
        self.datas_dir = get_path_with_glob(self.exec_path, base, img_dir)
        if '.DS_Store' in self.datas_dir:
            self.datas_dir.remove('.DS_Store')
        if len(image_tanks) >= 1:
            """ラベル2が複数存在する場合"""
            self.datas_wrapper = []
            target_dir = []
            for dir_name in self.datas_dir:
                if dir_name in image_tanks:
                    target_dir.append(dir_name)
            """ターゲットデータディレクトリ更新"""
            self.datas_dir = target_dir
        else:
            self.datas_wrapper = None

        self.labels = list(map(lambda label: label.split('_')[0], self.datas_dir))
        self.params = self.__read_yaml(get_path_with_glob(self.exec_path, base, 'param.yml'))
        # self.datas = get_path_with_glob(exec_path, base, '.+datas_dir[0] + '/*.{}'.format(self.params['crawler']['ext']))
        # self.img_dir_abspath = []
        # for idx, dir_name in enumerate(datas_dir):
        #     print('dir:', dir_name)
        #     self.img_dir_abspath.append(os.path.join(self.exec_path.split(base)[0], base, img_dir, dir_name))
        #     if idx == 0:
        #         self.datas = [self.img_dir_abspath[idx] + '/' + img_name for img_name in get_path_with_glob(self.exec_path, base, dir_name) if str(img_name) != 'fuzzies']
        #         self.datas.sort()
        #     else:
        #         self.oppo_datas = [self.img_dir_abspath[idx] + '/' + img_name for img_name in get_path_with_glob(self.exec_path, base, dir_name) if str(img_name) != 'fuzzies']
        #         self.oppo_datas.sort()
        #     print('finish. {}'.format(dir_name))

    def get_img_dir(self, target_label, split_tag=True):
        """
        imgフォルダのパスをターゲットとnot_targetに分けて取得
        :param target_label:
        :return:
        """
        here = '/'.join(inspect.stack()[0][1].split('/')[:-3])
        datas_abspath = os.path.join(here, 'data/img')
        img_dir = os.listdir(datas_abspath)
        if split_tag:
            target_dir = [d for d in img_dir if d.startswith(target_label)]
            not_target_dir = [d for d in img_dir if not d == target_dir[0]]
            result = (target_dir, not_target_dir)
        else:
            result = img_dir
        return result


    def read_datas_dir(self, target, not_target, target_label, multi_value_mode=False):
        # todo:
        #get_img_dir()を利用し、それぞれのフォルダごとに変数に画像のフルパスをリスト形式で格納する
        #multi_value_mode未実装
        """
        データ一覧を読み込む
        :return (target, not_target)
        """
        # kernel.py / data_handling / ml で3層掘り下げる
        here = '/'.join(inspect.stack()[0][1].split('/')[:-3])
        datas_abspath = os.path.join(here, 'data/img')
        target_img_fullpath = []
        not_target_img_fullpath = []

        for i, label in enumerate([target, not_target]):
            for d in label:
                full_path = os.path.join(datas_abspath, d)
                img_list = glob.glob(os.path.join(full_path, "*"))
                if i == 0:
                    #targetラベル
                    target_img_fullpath.append(img_list)
                else:
                    not_target_img_fullpath.append(img_list)

        for pathbox in [target_img_fullpath, not_target_img_fullpath]:
            pathbox = sorted(pathbox)

        return (target_img_fullpath, not_target_img_fullpath)

    def data_split(self, datas, validation=False):
        """
        データ分割
        :param datas: 分割対象のリスト
        :param validation:
        :return: 分割後のタプル
        """
        try:
            test_num = int(len(datas) * self.params['ml']['test_data_rate'])
            train_num = len(datas) - test_num
            self.x_train_raw = datas[:train_num]
            self.x_test_raw = datas[-test_num:]
        except Exception as err:
            sys.stdout.write(str(err))
        else:
            print('splitted datas. test:{test}  train:{train}'.format(test=len(self.x_train_raw), train=len(self.x_test_raw)))
            return (self.x_train_raw, self.x_test_raw)

    def data_preprocess_basic(self, splitted_datas, gray=True, size=(100,100), label=0, precision=np.float32):
        """
        単一語句のデータ前処理
        :param splited_datas:
        :param gray:
        :param size:
        :param label:
        :param precision:
        :return:
        """
        self.x_train = []
        self.y_train = []
        self.x_test = []
        self.y_test = []
        size = [self.params['ml']['img_size_xy']]*2 if not self.params['ml']['img_size_xy'] == None else size
        for tr_or_ts, valid in enumerate([splitted_datas[0], splitted_datas[1]]):
            for img_path in valid:
                try:
                    img = load_img(img_path, color_mode='grayscale', target_size=size)
                    img_bin = img_to_array(img)
                    # data_container[label].append(img_bin)
                    if tr_or_ts == 0:
                        self.x_train.append(img_bin)
                        self.y_train.append(label)
                        print('encoded img for train.[{}]'.format(img_path))
                    elif tr_or_ts == 1:
                        self.x_test.append(img_bin)
                        self.y_test.append(label)
                        print('encoded img for test.[{}]'.format(img_path))
                except:
                    print('cant preprocessed image.[{}]'.format(img_path))
                    continue
                else:
                    pass
            # self.x_train = list(map(lambda img_bin: np.float16(img_bin)/255, self.x_train))
            # self.x_test = list(map(lambda img_bin: np.float16(img_bin) / 255, self.x_test))
            self.x_train = list(map(lambda img_bin: np.ravel(precision(img_bin) / 255.0), self.x_train))
            self.x_test = list(map(lambda img_bin: np.ravel(precision(img_bin) / 255.0), self.x_test))
        print('data shape {}'.format(self.x_train[0].shape))
        print('train {}  test {}'.format(len(self.x_train), len(self.x_test)))

    def split_train_test(self, targets, not_targets):
        """
        :param targets:
        :param not_targets:
        :return:
        """

        here = '/'.join(inspect.stack()[0][1].split('/')[:-3])
        os.makedirs(os.path.join(here, 'data', '.prepare'), exist_ok=True)
        stack_dir = os.path.join(here, 'data', '.prepare')
        shutil.rmtree(stack_dir)
        makes = ['', 'train', 'validation']
        for work in makes:
            os.makedirs(os.path.join(stack_dir, work))
            if not work == '':
                try:
                    with open(os.path.join(stack_dir, work, 'label.txt'), 'x') as f:
                        f.write('')
                except FileExistsError:
                    pass

        # rateごとに各フォルダに配置する
        rate = self.params['ml']['test_data_rate']
        work_dir = None
        f_train = open(os.path.join(stack_dir, 'train', 'label.txt'), 'a')
        f_validation = open(os.path.join(stack_dir, 'validation', 'label.txt'), 'a')
        for i, label in enumerate([*targets, *not_targets]):
            for num, img in enumerate(label):
                if num < int(rate * len(label)):
                    #validationフォルダに入れる際
                    work_dir = 'validation'
                    write_label_file = f_validation
                else:
                    #trainフォルダに入れる際
                    work_dir = 'train'
                    write_label_file = f_train
                set_dir = os.path.join(stack_dir, work_dir)
                _ = shutil.move(img, set_dir)
                write_label_file.write(str(i) + '\n')
        f_train.close()
        f_validation.close()
        return os.path.join(stack_dir, 'train'), os.path.join(stack_dir, 'validation')


    def preprocess(self, train, valid, color_mode='grayscale'):
        """
        :param train: 学習用画像フォルダ
        :param valid: テスト用画像フォルダ
        :param color_mode: グレースケール推奨
        :return: ラベルの格納されたリスト
        """
        train_x = []
        test_x = []
        train_label_file = open(os.path.join(train, 'label.txt'), 'r')
        valid_label_file = open(os.path.join(valid, 'label.txt'), 'r')
        try:
            train_label = [int(label.strip()) for label in train_label_file.readlines()]
            valid_label = [int(label.strip()) for label in valid_label_file.readlines()]
        finally:
            train_label_file.close()
            valid_label_file.close()
        imgs = sorted(glob.glob(os.path.join(train, "*.png")))
        class_num = max(train_label) + 1
        for idx, img in enumerate(imgs):
            img_bin = img_to_array(load_img(img, color_mode=color_mode, target_size=(self.params['ml']['img_size_xy'], self.params['ml']['img_size_xy']))) / 255.0
            train_x.append(img_bin)
        train_y = to_categorical(train_label, num_classes=class_num)
        imgs = sorted(glob.glob(os.path.join(valid, "*.png")))
        for idx, img in enumerate(imgs):
            img_bin = img_to_array(load_img(img, color_mode=color_mode, target_size=(self.params['ml']['img_size_xy'], self.params['ml']['img_size_xy']))) / 255.0
            test_x.append(img_bin)
        test_y = to_categorical(valid_label, num_classes=class_num)
        train_x = np.array(train_x, dtype=np.float32)
        test_x = np.array(test_x, dtype=np.float32)

        return train_x, train_y, test_x, test_y


    # def data_preprocess(self, targets=[], not_targets=[], flatten=True, color_mode='grayscale'):
    #     """
    #     2つ以上の単語が与えられた際の前処理
    #     画像のフルパスを受け取る
    #     """
    #     def norm(x):
    #         try:
    #             x = np.asarray(x)
    #         except:
    #             pass
    #         finally:
    #             x = x.astype('float32')
    #             x /= 255.0
    #             return x
    #
    #     x = []
    #     y = []
    #     size = [self.params['ml']['img_size_xy']] * 2 if not self.params['ml']['img_size_xy'] == None else (100, 100)
    #     for idx, datas in enumerate([targets, not_targets]):
    #         for data in tqdm(datas):
    #             img_bin = img_to_array(load_img(data, color_mode=color_mode, target_size=size))
    #             x.append(img_bin)
    #             y.append(idx)
    #     y = np.asarray(y)
    #     if flatten:
    #         x = [np.ravel(img_bin) for img_bin in x]
    #     x = norm(x)
    #     # テストデータが完全に片方に固まってしまうバグの応急措置
    #     # ESSLが使えない
    #     self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=self.params['ml']['test_data_rate'])
    #     # self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=self.params['ml']['test_data_rate'], shuffle=False)
    #     processed_labels = self.__to_onehot([self.y_train, self.y_test])
    #     self.y_train, self.y_test = processed_labels
    #     return (self.x_train, self.x_test, self.y_train, self.y_test)

    def __to_onehot(self, labels, classes=2):
        processed_labels = []
        for label in labels:
            processed_labels.append(to_categorical(label, num_classes=classes))
        return processed_labels

    def __read_yaml(self, uri):
        import yaml
        try:
            with open(uri, 'r') as d:
                param_dict = yaml.load(d)
        except Exception as err:
            sys.stdout.write(str(err))
            return
        return param_dict


class OpponentImage():

    def __init__(self, target_dir, image_tanks, params):
        target_dir = target_dir[0] if target_dir != None else image_tanks[-1]
        self.img_path = os.path.join('/'.join(inspect.stack()[0][1].split('/')[:-3]), 'data/img')
        self.target_path = os.path.join(self.img_path, target_dir)
        self.decay = params['oppoimg']['decay']
        self.mode = params['oppoimg']['mode']
        self.ext = params['crawler']['ext']
        self.xy = params['ml']['img_size_xy']
        self.gray = True if params['ml']['grayscale'] else False
        # self.make_fuzzyimg(decay=self.decay, effect=self.mode)

    def make_noise(self):
        from . import effect_func as ef
        target = self.target_path
        effect = self.mode
        uniformly = False
        if effect == "all":
            uniformly = True
        size = self.xy
        grayscale = self.gray
        e_dict = {
            'srandom': lambda x: ef.simple_random(x),
            'mizutama': lambda x: ef.mizutama(x),
            'rect': lambda x: ef.discontinuous_random(x),
            'slice': lambda x: ef.slice(x),
        }
        self.labels = sorted(list(e_dict.keys()))

        try:
            imgs = sorted(os.listdir(target))
            imgs = [os.path.join(target, img) for img in imgs]
            # dir_path = self.make_noise_dir(effect_name=effect, target_name=target.split('/')[-1])
        except Exception as e:
            sys.stderr.write(e)
            print()
        finally:
            target_name = target.split('/')[-1]
            if uniformly == True:
                exec_effect = e_dict.keys()
            else:
                exec_effect = effect
            for e in exec_effect:
                print(e)
                dir_path = self.make_noise_dir(effect_name=e, target_name=target_name)
                for i, img_path in tqdm(enumerate(imgs)):
                    print(img_path)
                    img_bin = img_to_array(load_img(img_path, grayscale=grayscale, target_size=(size, size)))
                    # np.ravelは破壊的
                    # flat_img_bin = np.ravel(img_bin)
                    # effected_bin = e_dict[e](flat_img_bin).reshape(size, size, -1)
                    effected_bin = e_dict[e](img_bin).reshape(size, size, -1)
                    img_name = '{}_{:03}.{}'.format(e ,i, self.ext)
                    save_img(path=os.path.join(dir_path, img_name), x=effected_bin)

        return self.labels


    def make_noise_dir(self, effect_name, target_name):
        now = datetime.now()
        current_time = '{y}_{m}_{d}_{h}_{mi}_{s}'.format(y=str(now.year), m=str(now.month), d=str(now.day),
                                                          h=str(now.hour), mi=str(now.minute), s=str(now.second))

        identifier = 'n'
        dir_name = '{}_{}_{}_{}'.format(identifier, effect_name, target_name, current_time)
        dir_path = os.path.join(self.img_path, dir_name)
        try:
            os.makedirs(dir_path, exist_ok=True)
        except:
            return None
        finally:
            return dir_path


    def return_datafiles(self):
        self.y_train = to_categorical(self.y_train, num_classes=2)
        self.y_test = to_categorical(self.y_test, num_classes=2)
        return (self.x_train, self.x_test, self.y_train, self.y_test)

    def test_show(self, np_img):
        import matplotlib.pyplot as plt
        ex_img = array_to_img(np_img.reshape(100,100,1))
        ex_img.save('test.png')

    def __gc_vals(self, *objs):
        for rm_ival in objs:
            try:
                del rm_ival
            except:
                continue
        gc.collect()


# # kernel test
# if __name__ == '__main__':
#     k = Kernel()
#     k.data_split()
#     k.data_preprocess_basic()
#     oppi = OpponentImage()
#     datasets = oppi.return_datafiles()