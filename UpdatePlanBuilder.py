import json
import zipfile

from PyQt5.QtCore import QThread, pyqtSignal


class UpdatePlanBuilder(QThread):
    update_plan_ready = pyqtSignal(list)  # 信号，用于通知主线程处理完成

    def __init__(self, zip_path):
        super().__init__()
        self.zip_path = zip_path
        self.data = {}
        self.manifest = {}
    def run(self):
        # 在后台线程中执行文件加载和更新计划生成
        self.load_manifest_and_bins_from_zip()



    def load_manifest_and_bins_from_zip(self):
        print("load_manifest_and_bins_from_zip:-------------------")
        # 打开 ZIP 文件
        with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
            # 读取 manifest.json 文件
            try:
                # 获取所有文件的名称列表
                file_list = zip_file.namelist()

                # 找到包含 manifest.json 的文件路径
                manifest_path = next((f for f in file_list if f.endswith('manifest.json')), None)
                print("load_manifest_and_bins_from_zip manifest_path:",manifest_path)
                if manifest_path:
                    # 读取 manifest.json 文件
                    with zip_file.open(manifest_path) as manifest_file:
                        manifest_json = json.load(manifest_file)
                        print("self.manifest=", manifest_json)
                        self.data['manifest'] = manifest_json
                        # self.manifest = manifest_json

                        # 从 manifest 中读取 platform, app 和 bins 信息
                        bins = []
                        if 'bins' in manifest_json:
                            for bin_info in manifest_json.get('bins', []):
                                bin_name = bin_info['name']
                                bin_info['data'] = self.read_bin_file(zip_file, bin_name)
                                bins.append(bin_info)
                        if 'platform_merge_app' in manifest_json:
                            self.data['platform_merge_app'] = {
                                "name": manifest_json['platform_merge_app']['name'],
                                "address": manifest_json['platform_merge_app']['address'],
                                "platform_version": manifest_json['platform_merge_app']['platform_version'],
                                "app_version": manifest_json['platform_merge_app']['app_version'],
                                "data": self.read_bin_file(zip_file, manifest_json['platform_merge_app']['name'])
                            }
                        else:
                            # 加载 platform 和 app 文件数据
                            if 'platform' in manifest_json:
                                self.data['platform'] = {
                                    "name": manifest_json['platform']['name'],
                                    "address": manifest_json['platform']['address'],
                                    "version": manifest_json['platform']['version'],
                                    "data": self.read_bin_file(zip_file, manifest_json['platform']['name'])
                                }
                            if 'app' in manifest_json:
                                self.data['app'] = {
                                    "name": manifest_json['app']['name'],
                                    "address": manifest_json['app']['address'],
                                    "version": manifest_json['app']['version'],
                                    "data": self.read_bin_file(zip_file, manifest_json['app']['name'])
                                }

                        # 保存所有 bins 信息
                        self.data['bins'] = bins
                        # print("Loaded manifest and bins:",  self.manifest)
            except Exception as e:
                print(f"解压时出错: {str(e)}")
                print(f"Error: {self.zip_path} not found in zip.")





    def read_bin_file(self, zip_file, bin_name):
        """从 ZIP 文件中读取 bin 文件数据"""
        """从 ZIP 文件中读取 bin 文件数据，支持多级目录"""
        try:
            # 遍历 ZIP 文件中的所有路径，找到 bin 文件的实际路径
            bin_path = next((f for f in zip_file.namelist() if f.endswith(bin_name)), None)
            print("read_bin_file-----:", bin_path)
            if bin_path:
                with zip_file.open(bin_path) as bin_file:
                    # while True:
                    #     chunk = bin_file.read(200)
                    #     if not chunk:
                    #         print("文件发送完成")
                    #         break
                    #     print(f"发送了 {len(chunk)} 字节数据: {chunk.hex().upper()}")

                    return bin_file.read()

            else:
                print(f"Error: {bin_name} not found in zip.")
                return None
        except KeyError:
            print(f"Error accessing {bin_name} in zip.")
            return None




