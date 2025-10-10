SET s3_endpoint='idmlakehouse.tmslab.cn';
SET s3_url_style='path';
SET s3_use_ssl='false';
--SET s3_access_key_id='0Mz9gdbJk37aEKAEt6OV';
--SET s3_secret_access_key='Vu27z09Uml5Jd57EXRFepZuOTZmoGKctePO6nAhA';

ATTACH 'ducklake:pred_demo.ducklake' as hea (
    DATA_PATH 's3://idmdatabase/hea_pred_demo'
);

use hea;
