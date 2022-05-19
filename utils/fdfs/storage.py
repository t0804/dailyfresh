from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    # 自定义文件存储
    def __init__(self, client_conf=None, base_url=None):
        if client_conf is None:
            client_conf = settings.DEFAULT_FDFS_CLIENT_CONF
        self.client_conf = client_conf
        if base_url is None:
            base_url = settings.DEFAULT_FDFS_BASE_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        # 打开文件方法
        pass

    def _save(self, name, content):
        # name : 上传的文件名
        # content : 包含上传文件内容的File对象
        # 实例化fdfs_client对象
        client = Fdfs_client(self.client_conf)
        # 通过文件内容上传
        res = client.upload_by_buffer(content.read())
        '''
        return dict
        {
            'Group name': group_name,
            'Remote file_id': remote_file_id,
            'Status': 'Upload successed.',
            'Local file name': '',
            'Uploaded size': upload_size,
            'Storage IP': storage_ip
        } if success else None
        '''
        if res.get('Status') != 'Upload successed.':
            # 返回的Status不是Upload successed.说明上传失败
            raise Exception('--- fdfs upload failed!')
        filename = res.get('Remote file_id')
        # 返回文件名（fdfs的文件id）
        return filename

    def exists(self, name):

        # 名称永远可用直接返回False
        return False

    def url(self, name):
        # nginx = 'http://192.168.47.131:8888/'
        return self.base_url + name
