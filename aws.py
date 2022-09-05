from credentials import AWSSecretKey, AWSAccessKeyId
import boto3
from credentials import AWSAccessKeyId,AWSSecretKey

# print(boto3.__version__)

ddb_client = boto3.client(
    'dynamodb',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

ddb_resource = boto3.resource(
    'dynamodb',
    region_name ='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

s3_client = boto3.client(
    's3',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

s3_resource = boto3.resource(
    's3',
    region_name = 'ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)


TABLE_NAME = "face_recog_db"
EMP_TABLE = "emp_db"
s3_bucket_encods = s3_resource.Bucket(name="encods")
s3_bucket_files = s3_resource.Bucket(name="npzfiles")

table_emp = ddb_resource.Table(EMP_TABLE)
table = ddb_resource.Table(TABLE_NAME)


##### Fetching dynammo db details

dates_dict = {}
id_dict = {}
raw_dict = {}
dict_ = {}


def emp_dictionary_fetch() -> dict:
    """
    Sends a dict with date as the keys
    """

    response = table.scan()
    items_list = response['Items']

    for i in range(len(items_list)):
        date = items_list[i]["DATE_KEY"]
        id = items_list[i]["ID_KEY"]

        if date in dates_dict:
            dates_dict[date][items_list[i]["ID_KEY"]] = items_list[i]
        else:
            dates_dict[date] = {}
            dates_dict[date][items_list[i]["ID_KEY"]] = items_list[i]

        if id in id_dict:
            id_dict[id][date] = items_list[i]
        else:
            id_dict[id] = {}
            id_dict[id][date] = items_list[i]


    dict_["ID"] = id_dict
    dict_["DATE"] = dates_dict
    dict_["DATA"] = items_list

    return dict_
    
#####




#####
 
# encods_list = []
# names_list = []

# def access_encods():
#     for files in s3_bucket.objects.all():
#         file = files.get()['Body'].read().decode('utf-8')
#         json_ = json.loads(file)

#         print(json_)






