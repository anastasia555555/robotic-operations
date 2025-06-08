import os
import sys
import argparse

import cv2
import numpy as np
from google.protobuf.json_format import MessageToJson

import app.services.dicom_analysis_grpc.visualising_scripts.analysis_result_pb2 as pb2


def parse_args():
    p = argparse.ArgumentParser(
        description="Read a serialized AnalysisResult (.pb) and print contents."
    )
    p.add_argument("input_pb",
                   help="Path to the binary AnalysisResult file (e.g. result.pb)")
    p.add_argument("--to-json", action="store_true",
                   help="Also dump JSON representation to stdout")
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.input_pb):
        print(f"Error: file not found: {args.input_pb}", file=sys.stderr)
        sys.exit(1)

    result = pb2.AnalysisResult()
    with open(args.input_pb, "rb") as f:
        result.ParseFromString(f.read())

    print("=== AnalysisResult ===")
    print(f"Image path: {result.image_path}")
    print(f"Dimensions: {result.width} x {result.height}")
    print(f"Total inference time: {result.total_inference_time:.4f} s")
    print(f"Number of instances: {len(result.instances)}\n")

    for inst in result.instances:
        print(f"--- Instance #{inst.id} ---")
        print(f"Class       : {inst.class_name}")
        print(f"Score       : {inst.score:.4f}")
        print(f"BBox (xywh) : ({inst.bbox.x:.3f}, {inst.bbox.y:.3f}, "
              f"{inst.bbox.width:.3f}, {inst.bbox.height:.3f})")

        mask_array = np.frombuffer(inst.mask_png, dtype=np.uint8)
        mask = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            print("  [Warning] failed to decode PNG mask")
        else:
            print(f"Mask shape  : {mask.shape}")
        print()

    if args.to_json:
        json_path = os.path.splitext(args.input_pb)[0] + ".json"
        json_str = MessageToJson(result)
        with open(json_path, "w", encoding="utf-8") as jf:
            jf.write(json_str)
        print(f"JSON written to {json_path}")


if __name__ == "__main__":
    main()