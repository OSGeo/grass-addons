import logging
import os

from hdfs import InsecureClient, HdfsError

from base_hook import BaseHook

_kerberos_security_mode = None  # TODO make confugration file for this
if _kerberos_security_mode:
    try:
        from hdfs.ext.kerberos import KerberosClient
    except ImportError:
        logging.error("Could not load the Kerberos extension for the WebHDFSHook.")
        raise


class WebHDFSHook(BaseHook):
    """
    Interact with HDFS. This class is a wrapper around the hdfscli library.
    """

    def __init__(self, webhdfs_conn_id='webhdfs_default', proxy_user=None):
        self.webhdfs_conn_id = webhdfs_conn_id
        self.proxy_user = proxy_user

    def get_conn(self):
        """
        Returns a hdfscli InsecureClient object.
        """
        nn_connections = self.get_connections(self.webhdfs_conn_id)
        for nn in nn_connections:
            try:
                logging.debug('Trying namenode {}'.format(nn.host))
                connection_str = 'http://{nn.host}:{nn.port}'.format(nn=nn)
                if _kerberos_security_mode:
                    client = KerberosClient(connection_str)
                else:
                    proxy_user = self.proxy_user or nn.login
                    client = InsecureClient(connection_str, user=proxy_user)
                client.status('/')
                logging.debug('Using namenode {} for hook'.format(nn.host))
                return client
            except HdfsError as e:
                logging.debug("Read operation on namenode {nn.host} failed with"
                              " error: {e.message}".format(**locals()))
        nn_hosts = [c.host for c in nn_connections]
        no_nn_error = "Read operations failed on the namenodes below:\n{}".format("\n".join(nn_hosts))
        raise Exception(no_nn_error)

    def test(self):
        try:
            path = self.check_for_path("/")
            print('***' * 30)
            print("\n   Test <webhdfs> connection (is path exists: ls /) \n    %s \n" % path)
            print('***' * 30)
            return True

        except Exception, e:
            print("\n     ERROR: connection can not be established: %s" % e)
            print('***' * 30)
            return False

    def check_for_path(self, hdfs_path):
        """
        Check for the existence of a path in HDFS by querying FileStatus.
        """
        c = self.get_conn()
        return bool(c.status(hdfs_path, strict=False))

    def check_for_content(self, hdfs_path, recursive=False):

        c = self.get_conn()
        return c.list(hdfs_path, status=recursive)

    def progress(self, a, b):
        # print(a)
        print('progress: chunk_size %s' % b)

    def upload_file(self, source, destination, overwrite=True, parallelism=1,
                    **kwargs):
        """
        Uploads a file to HDFS
        :param source: Local path to file or folder. If a folder, all the files
          inside of it will be uploaded (note that this implies that folders empty
          of files will not be created remotely).
        :type source: str
        :param destination: PTarget HDFS path. If it already exists and is a
          directory, files will be uploaded inside.
        :type destination: str
        :param overwrite: Overwrite any existing file or directory.
        :type overwrite: bool
        :param parallelism: Number of threads to use for parallelization. A value of
          `0` (or negative) uses as many threads as there are files.
        :type parallelism: int
        :param \*\*kwargs: Keyword arguments forwarded to :meth:`upload`.
        """
        c = self.get_conn()
        c.upload(hdfs_path=destination,
                 local_path=source,
                 overwrite=overwrite,
                 n_threads=parallelism,
                 progress=self.progress,
                 **kwargs)
        logging.debug("Uploaded file {} to {}".format(source, destination))

    def download_file(self, hdfs_path, local_path, overwrite=True, parallelism=1,
                      **kwargs):

        c = self.get_conn()
        out=c.download(hdfs_path=hdfs_path,
                   local_path=local_path,
                   overwrite=overwrite,
                   n_threads=parallelism,
                   **kwargs)

        logging.debug("Download file {} to {}".format(hdfs_path, local_path))


        return out

    def mkdir(self, path, **kwargs):
        c = self.get_conn()
        c.makedirs(hdfs_path=path, **kwargs)

        logging.debug("Mkdir file {} ".format(path))

    def write(self, fs, hdfs, **kwargs):
        client = self.get_conn()

        client.delete(hdfs, recursive=True)
        model = {
            '(intercept)': 48.,
            'first_feature': 2.,
            'second_feature': 12.,
        }

        with client.write(hdfs, encoding='utf-8') as writer:
            for item in model.items():
                writer.write(u'%s,%s\n' % item)
