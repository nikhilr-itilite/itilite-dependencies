Use this library for connecting with S3.
It supports two operations

    1. save_to_s3

        :param bucket_name: Name of the S3 bucket.
        :param file_name: Name of the S3 file.
        :param data: Data which is being saved to S3

    2. read_from_s3

        :param bucket_name: S3 bucket name
        :param file_name: file name where payload is present