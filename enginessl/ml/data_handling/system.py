from . import kernel


class DataHandling(kernel.OpponentImage ,kernel.Kernel):

    def __init__(self, target_label, image_tanks=[]):
        print('Data processing execution.')
        # self.oppo = kernel.OpponentImage(image_tanks)
        self.data_handling = kernel.Kernel(image_tanks)
        # print('labels :{}'.format(self.oppo.labels))

    def get_builtup_data(self,targets=[], not_targets=[], color_mode='grayscale'):
        """
        画像のフルパスを受け取る
        :return: 正規化されたデータ、ラベル
        """
        train, valid = self.data_handling.split_train_test(targets=targets, not_targets=not_targets)
        return self.data_handling.preprocess(train=train, valid=valid, color_mode=color_mode)

    def get_label_name(self):
        self.data_handling

    def read_dirs(self, target_label):
        """
        :return: target type=list
                    ターゲット画像のリストをくるんだリスト
                    target[0]で取り出す
                    0dimensionには基本的に1要素しか入らないがnot_targetの形状を考慮しそちらの形状で揃えた

                 not_target type=list
                    ターゲット以外の画像のリストをくるんだリスト
                    not_target[index]で各ノイズにアクセスできる
                    ノイズ一つ一つもリストになっていて、そのまま一つのラベルとして使用する

        """
        target_dir, not_target_dir = self.get_img_dir(target_label=target_label, split_tag=True)
        return self.read_datas_dir(target=target_dir, not_target=not_target_dir, target_label=target_label)

    def oppo_kernel(self, target_dir, image_tanks):
        print('Noise data processing execution.')
        self.oppo = kernel.OpponentImage(target_dir=target_dir ,image_tanks=image_tanks, params=self.data_handling.params)
        return self.oppo

    def make_noise(self, target):
        print('Making noise data.')
        labels = self.oppo.make_noise()
        return labels.insert(0, target)

    def get_builtup_data_include_noise(self):
        """
        :return: tuple (self.x_train, self.x_test, self.y_train, self.y_test)
        """
        return self.oppo.return_datafiles()

    def test_show(self, img_bin):
        self.oppo.test_show(img_bin)