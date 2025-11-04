SET s3_endpoint='idmlakehouse.tmslab.cn';
SET s3_url_style='path';
SET s3_use_ssl='false';

ATTACH 'ducklake:http://idmlakehouse.tmslab.cn/idmdatabase/metadata/hea_6.ducklake' as hea (
    DATA_PATH 's3://idmdatabase/hea'
);

use hea;