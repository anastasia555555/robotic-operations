# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: dicom_analysis_service.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'dicom_analysis_service.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1c\x64icom_analysis_service.proto\x12\x05\x64icom\"4\n\x0f\x41nalysisRequest\x12\x0f\n\x07i_dicom\x18\x01 \x01(\x05\x12\x10\n\x08zip_data\x18\x02 \x01(\x0c\"4\n\x10\x41nalysisResponse\x12\x0f\n\x07i_dicom\x18\x01 \x01(\x05\x12\x0f\n\x07np_data\x18\x02 \x01(\x0c\x32L\n\x0e\x44ICOM_Analyser\x12:\n\x07\x41nalyze\x12\x16.dicom.AnalysisRequest\x1a\x17.dicom.AnalysisResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dicom_analysis_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_ANALYSISREQUEST']._serialized_start=39
  _globals['_ANALYSISREQUEST']._serialized_end=91
  _globals['_ANALYSISRESPONSE']._serialized_start=93
  _globals['_ANALYSISRESPONSE']._serialized_end=145
  _globals['_DICOM_ANALYSER']._serialized_start=147
  _globals['_DICOM_ANALYSER']._serialized_end=223
# @@protoc_insertion_point(module_scope)
