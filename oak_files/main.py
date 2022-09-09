# coding=utf-8
import time
import blobconverter
import boto3
import cv2
import io
import depthai as dai
import numpy as np
from datetime import date, datetime

VIDEO_SIZE = (1072, 1072)

BLOB_PATH_FACE_DET = "data\face-detection-retail-0004_openvino_2021.2_4shave.blob"
BLOB_PATH_POSE_EST = "data\head-pose-estimation-adas-0001_openvino_2021.2_4shave.blob"
BLOB_PATH_FACE_RECOG = "data\face-recognition-mobilefacenet-arcface_2021.2_4shave.blob"

#### credentials ####
AWSAccessKeyId = 'AKIAZTBLXFPX3NJHL73W'
AWSSecretKey = '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'
#### aws connections ####

client = boto3.client(
    'dynamodb',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

client = boto3.resource(
    'dynamodb',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

s3_client = boto3.client(
    's3',
    region_name = 'ap-south-1',
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

table_emp = client.Table(EMP_TABLE)
table = client.Table(TABLE_NAME)

s3_bucket = s3_resource.Bucket(name="divineai")
s3_encods_filter = s3_bucket.objects.filter(Prefix = 'encods/')
s3_npzfiles_filter = s3_bucket.objects.filter(Prefix = 'npzfiles/')


##### fetching the employee dict ####
def get_emp_dict():
    emp_id_dict = {}
    response = table_emp.scan()
    data = response['Items']
    
    for i in range(len(data)):
        each_emp_dict = response['Items'][i]
        EMP_ID = each_emp_dict['EMP_ID']
        NAME_KEY = each_emp_dict['NAME_KEY']
        emp_id_dict[NAME_KEY] = EMP_ID

    return emp_id_dict



def frame_norm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


class TextHelper:
    def __init__(self) -> None:
        self.bg_color = (0, 0, 0)
        self.color = (255, 255, 255)
        self.text_type = cv2.FONT_HERSHEY_SIMPLEX
        self.line_type = cv2.LINE_AA

    def putText(self, frame, text, coords):
        cv2.putText(frame, text, coords, self.text_type, 1.0, self.bg_color, 4, self.line_type)
        cv2.putText(frame, text, coords, self.text_type, 1.0, self.color, 2, self.line_type)

class FaceRecognition:
    def __init__(self) -> None:
        self.read_db()
        self.bg_color = (0, 0, 0)
        self.color = (255, 255, 255)
        self.text_type = cv2.FONT_HERSHEY_SIMPLEX
        self.line_type = cv2.LINE_AA
        self.printed = True

    def cosine_distance(self, a, b) -> float:
        if a.shape != b.shape:
            raise RuntimeError("array {} shape not match {}".format(a.shape, b.shape))
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        return np.dot(a, b.T) / (a_norm * b_norm)

    def new_recognition(self, results) -> str:
        """
        new recognition
        """
        conf = []
        max_ = 0
        label_ = None

        for label in list(self.labels):
            for j in self.db_dic.get(label):
                conf_ = self.cosine_distance(j, results)
                if conf_ > max_:
                    max_ = conf_
                    label_ = label

        conf.append((max_, label_))
        name = conf[0] if conf[0][0] >= 0.5 else (1 - conf[0][0], "stranger")
        # if name[1] == "stranger":
        #     self.create_db(results)
        
        return name

    def read_db(self):
        """
        Reading the arrays and npz files
        accessing from AWS S3 Bucket
        """

        self.labels = [] #The labels has the respective names
        self.db_dic = {} #The dict has the arrays in values with names as keys

        for files in s3_bucket.objects.all():
            if files not in s3_encods_filter and files.key != 'npzfiles/':
                full_filename_key = files.key
                filename = full_filename_key[9:-4]
                self.labels.append(filename)

                with io.BytesIO(files.get()['Body'].read()) as f:
                    f.seek(0)
                    db = np.load(f)
                    db_list = []
                    try:arrays = list(db.keys())
                    except: pass
                    for arr in arrays:
                        try:
                            value_list = db[arr]
                        except: pass
                        try: db_list.append(value_list)
                        except: pass
                    self.db_dic[filename] = np.array(db_list) 
    

    def putText(self, frame, text, coords):
        cv2.putText(frame, text, coords, self.text_type, 1, self.bg_color, 4, self.line_type)
        cv2.putText(frame, text, coords, self.text_type, 1, self.color, 1, self.line_type)


#################

class TwoStageHostSeqSync:

    def __init__(self) -> None:
        self.msgs = {}
    
    def add_msg(self, msg, name) -> None:
        
        seq = str(msg.getSequenceNum())

        if seq not in self.msgs:
            self.msgs[seq] = {}

        if "recognition" not in self.msgs[seq]:
            self.msgs[seq]["recognition"] = []

        if name == "recognition":
            self.msgs[seq]["recognition"].append(msg)

        elif name == "detection":
            self.msgs[seq][name] = msg
            self.msgs[seq]["len"] = len(msg.detections)

        elif name == "color":
            # Save color frame in the directory
            self.msgs[seq][name] = msg
            


    def get_msgs(self) -> str:
        seq_remove = [] # Arr of sequence numbers to get deleted

        for seq, msgs in self.msgs.items():
            # Will get removed from dict if we find synced msgs pair
            seq_remove.append(seq) 

            # Check if we have both detections and color frame with this sequence number
            if "color" in msgs and "len" in msgs:

                # Check if all detected objects (faces) have finished recognition inference
                if msgs["len"] == len(msgs["recognition"]):

                    # We have synced msgs, remove previous msgs (memory cleaning)
                    for rm in seq_remove:
                        del self.msgs[rm]

                    return msgs # Returned synced msgs

        return None


##### Pipeline ####

print("Creating pipeline...")
pipeline = dai.Pipeline()

print("Creating Color Camera...")
cam = pipeline.create(dai.node.ColorCamera)
# For ImageManip rotate you need input frame of multiple of 16
cam.setPreviewSize(1072, 1072)
cam.setVideoSize(VIDEO_SIZE)
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam.setInterleaved(False)
cam.setBoardSocket(dai.CameraBoardSocket.RGB)

host_face_out = pipeline.create(dai.node.XLinkOut)
host_face_out.setStreamName('color')
cam.video.link(host_face_out.input)

# ImageManip as a workaround to have more frames in the pool.
# cam.preview can only have 4 frames in the pool before it will
# wait (freeze). Copying frames and setting ImageManip pool size to
# higher number will fix this issue.
copy_manip = pipeline.create(dai.node.ImageManip)
cam.preview.link(copy_manip.inputImage)
copy_manip.setNumFramesPool(20)
copy_manip.setMaxOutputFrameSize(1072*1072*3)

# ImageManip that will crop the frame before sending it to the Face detection NN node
face_det_manip = pipeline.create(dai.node.ImageManip)
face_det_manip.initialConfig.setResize(300, 300)
copy_manip.out.link(face_det_manip.inputImage)

# NeuralNetwork
print("Creating Face Detection Neural Network...")
face_det_nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
face_det_nn.setConfidenceThreshold(0.5)
face_det_nn.setBlobPath(blobconverter.from_zoo(name="face-detection-retail-0004", shaves=6))
# Link Face ImageManip -> Face detection NN node
face_det_manip.out.link(face_det_nn.input)

face_det_xout = pipeline.create(dai.node.XLinkOut)
face_det_xout.setStreamName("detection")
face_det_nn.out.link(face_det_xout.input)

# Script node will take the output from the face detection NN as an input and set ImageManipConfig
# to the 'age_gender_manip' to crop the initial frame
script = pipeline.create(dai.node.Script)
script.setProcessor(dai.ProcessorType.LEON_CSS)

face_det_nn.out.link(script.inputs['face_det_in'])
# We also interested in sequence number for syncing
face_det_nn.passthrough.link(script.inputs['face_pass'])

copy_manip.out.link(script.inputs['preview'])
script.setScript("""
    
    import time
    sync = {}
    def get_sync(target_seq):
        seq_remove = [] # Arr of sequence numbers to get deleted
        for seq, msgs in sync.items():
            if seq == str(target_seq):
                for rm in seq_remove:
                    del sync[rm]
                return msgs
                
            seq_remove.append(seq) 
            
        return None
        
    def find_frame(target_seq):
        if str(target_seq) in sync:
            return sync[str(target_seq)]["frame"]
    
    def add_detections(det, seq):
        if len(det) == 0:
            del sync[str(seq)]
        else:
            sync[str(seq)]["detections"] = det
            
            
    def correct_bb(bb):
        if bb.xmin < 0: bb.xmin = 0.001
        if bb.ymin < 0: bb.ymin = 0.001
        if bb.xmax > 1: bb.xmax = 0.999
        if bb.ymax > 1: bb.ymax = 0.999
        
    while True:
        time.sleep(0.001)
        preview = node.io['preview'].tryGet()
        if preview is not None:
            sync[str(preview.getSequenceNum())] = {}
            sync[str(preview.getSequenceNum())]["frame"] = preview

        face_dets = node.io['face_det_in'].tryGet()
        if face_dets is not None:
            passthrough = node.io['face_pass'].get()
            seq = passthrough.getSequenceNum()
        
            if len(sync) == 0: continue
            img = find_frame(seq) # Matching frame is the first in the list
            if img is None: continue

            add_detections(face_dets.detections, seq)

            for det in face_dets.detections:
                cfg = ImageManipConfig()
                correct_bb(det)
                cfg.setCropRect(det.xmin, det.ymin, det.xmax, det.ymax)
                cfg.setResize(60, 60)
                cfg.setKeepAspectRatio(False)
                node.io['manip_cfg'].send(cfg)
                node.io['manip_img'].send(img)
                
        headpose = node.io['headpose_in'].tryGet()
        if headpose is not None:
            passthrough = node.io['headpose_pass'].get()
            seq = passthrough.getSequenceNum()
            
            r = headpose.getLayerFp16('angle_r_fc')[0] # Only 1 float in there

            msgs = get_sync(seq)
            bb = msgs["detections"].pop(0)
            correct_bb(bb)

            img = msgs["frame"]

            cfg = ImageManipConfig()
            rr = RotatedRect()
            rr.center.x = (bb.xmin + bb.xmax) / 2
            rr.center.y = (bb.ymin + bb.ymax) / 2
            rr.size.width = bb.xmax - bb.xmin
            rr.size.height = bb.ymax - bb.ymin
            rr.angle = r 
            cfg.setCropRotatedRect(rr, True)
            cfg.setResize(112, 112)
            cfg.setKeepAspectRatio(True)

            node.io['manip2_cfg'].send(cfg)
            node.io['manip2_img'].send(img)
""")

print("Creating Head pose estimation NN")
headpose_manip = pipeline.create(dai.node.ImageManip)
headpose_manip.initialConfig.setResize(60, 60)
headpose_manip.setWaitForConfigInput(True)
script.outputs['manip_cfg'].link(headpose_manip.inputConfig)
script.outputs['manip_img'].link(headpose_manip.inputImage)

headpose_nn = pipeline.create(dai.node.NeuralNetwork)
headpose_nn.setBlobPath(blobconverter.from_zoo(name="head-pose-estimation-adas-0001", shaves=6))
headpose_manip.out.link(headpose_nn.input)

headpose_nn.out.link(script.inputs['headpose_in'])
headpose_nn.passthrough.link(script.inputs['headpose_pass'])

print("Creating face recognition ImageManip/NN")

face_rec_manip = pipeline.create(dai.node.ImageManip)
face_rec_manip.initialConfig.setResize(112, 112)
face_rec_manip.setWaitForConfigInput(True)

script.outputs['manip2_cfg'].link(face_rec_manip.inputConfig)
script.outputs['manip2_img'].link(face_rec_manip.inputImage)

face_rec_nn = pipeline.create(dai.node.NeuralNetwork)
face_rec_nn.setBlobPath(blobconverter.from_zoo(name="face-recognition-arcface-112x112", zoo_type="depthai", shaves=6))
face_rec_manip.out.link(face_rec_nn.input)

arc_xout = pipeline.create(dai.node.XLinkOut)
arc_xout.setStreamName('recognition')
face_rec_nn.out.link(arc_xout.input)


with dai.Device(pipeline) as device:
    facerec = FaceRecognition()
    sync = TwoStageHostSeqSync()
    text = TextHelper()

    emp_id_dict = get_emp_dict()

    queues = {}
    # Create output queues
    for name in ["color", "detection", "recognition"]:
        queues[name] = device.getOutputQueue(name)

    name_dic = {}
    while True:
        for name, q in queues.items():

            if q.has():
                sync.add_msg(q.get(), name) 

        msgs = sync.get_msgs()
        if msgs is not None:
            frame = msgs["color"].getCvFrame()
            dets = msgs["detection"].detections

            for i, detection in enumerate(dets):
                bbox = frame_norm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (10, 245, 10), 2)

                features = np.array(msgs["recognition"][i].getFirstLayerFp16())
                conf, name_ = facerec.new_recognition(features)

                if name_ not in name_dic and name_ != 'stranger':

                    if (conf*100) > 80:
                        name_dic[name_] = conf
                        time = datetime.now()
                        date = str(datetime.now().date())
                        id = emp_id_dict[name_]
                        time_ = str(time.strftime('%I:%M:%S %p'))
                        hour = int(time.strftime("%H"))
                        
                        if(hour < 18):
                            table.put_item(
                                Item = {
                                    'DATE_KEY': date,
                                    'ID_KEY': id,
                                    'name': name_,
                                    'confidence': str(conf),
                                    'login_time': time_,
                                    'login_time_hour':str(hour),
                                    'logout_time':'NA',
                                    'hours':'NA',
                                }
                            )
                        else:
                            response = table.get_item(
                                Key={
                                    'DATE_KEY': date,
                                    'ID_KEY': id,
                                    }
                                )

                            table.update_item(
                                Key = {
                                    'DATE_KEY': date,
                                    'ID_KEY': id,
                                },
                                UpdateExpression="set logout_time = :logout AND hours = :hour",
                                ExpressionAttributeValues = {
                                    ':logout' : time_,
                                    ':hour'  : str(int(response['login_time_hour']) - hour),
                                },
                                ReturnValues="UPDATED_NEW",
                            ) 

                        text.putText(frame, f"Done", (bbox[0] + 10, bbox[1] + 35)) 
                
                
                text.putText(frame, f"{name_} {(100*conf):.0f}%", (bbox[0] + 10,bbox[1] + 35))

            cv2.imshow("color", cv2.resize(frame, (800,800)))

        if cv2.waitKey(1) == ord('q'):
            break