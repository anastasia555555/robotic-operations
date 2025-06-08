import grpc
import os
from google.protobuf.json_format import MessageToJson

from app.services.dicom_analysis_grpc import dicom_analysis_service_pb2 as pb2
from app.services.dicom_analysis_grpc import dicom_analysis_service_pb2_grpc as pb2_grpc
from app.services.dicom_analysis_grpc.visualising_scripts import analysis_result_pb2 as result_pb2
from app.database.db_connect import config

CURRENT_DIR = os.path.dirname(__file__)
APP_ROOT = os.path.dirname(CURRENT_DIR)
NP_STORAGE_DIR = os.path.join(APP_ROOT, config["NP_STORAGE_DIR"])
JSON_STORAGE_DIR = os.path.join(APP_ROOT, config["JSON_STORAGE_DIR"])
os.makedirs(NP_STORAGE_DIR, exist_ok=True)
os.makedirs(JSON_STORAGE_DIR, exist_ok=True)

def get_dicom_analysis(i_dicom: int, file_name: str, dicom_file_path: str):
    with grpc.insecure_channel(
        '10.243.50.135:50051',
        options=[
            ('grpc.max_send_message_length', 500 * 1024 * 1024),
            ('grpc.max_receive_message_length', 500 * 1024 * 1024)
        ]
    ) as channel:
        stub = pb2_grpc.DICOM_AnalyserStub(channel)

        with open(dicom_file_path, "rb") as f:
            zip_bytes = f.read()

        request = pb2.AnalysisRequest(
            i_dicom=i_dicom,
            zip_data=zip_bytes
        )
        response = stub.Analyze(request)


        base_name = file_name.removesuffix(".zip")
        

        pb_path = os.path.join(NP_STORAGE_DIR, f"{base_name}.pb")
        with open(pb_path, "wb") as np_file:
            np_file.write(response.np_data)


        result = result_pb2.AnalysisResult()
        with open(pb_path, "rb") as f:
            result.ParseFromString(f.read())

        json_str = MessageToJson(result)
        json_path = os.path.join(JSON_STORAGE_DIR, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            jf.write(json_str)

        return pb_path, json_path
