"""Python script to download model binaries.

Usage:
   python download_model.py --model <model_id> --QM <method>

Example commandline:
   python download_model.py --model LLaMA_7B_2_chat --QM QM_ARM
"""
import argparse
import hashlib
import os
import zipfile

import requests
from tqdm import tqdm

MODEL_DIR = "models"

# URLs and md5sums for models
models = {
    "LLaMA_7B_fp32": {
        "url": "https://www.dropbox.com/scl/fi/xli03zmet80vxrib7tuq7/LLaMA_7B.zip?rlkey=98e2vvptmn6qz0fw2uudd3gb1&dl=1",  # noqa: E501
        "md5sum": "1ef6fde9b90745fa4c3d43e6d29d0c53",
    },
    "LLaMA2_7B_chat_fp32": {
        "url": "https://www.dropbox.com/scl/fi/55hei425f6tiev9cc9h9r/LLaMA_7B_2_chat.zip?rlkey=42j8vp7d3crz6qm9om23vth25&dl=1",  # noqa: E501
        "md5sum": "fccbd388c1e89dd90e153ed6d9734189",
    },
    "LLaMA2_13B_chat_fp32": {
        "url": "https://www.dropbox.com/scl/fi/qpzv3805ftdldvlocssu4/LLaMA_13B_2_chat.zip?rlkey=tfgnv9cz2i8lwuznyy6u3sf4k&dl=1",  # noqa: E501
        "md5sum": "59b73efa638be4131e5fd27c3fdee597",
    },
    "CodeLLaMA_7B_Instruct_fp32": {
        "url": "https://www.dropbox.com/scl/fi/fo79fi1q395rfb8lu4bef/CodeLLaMA_7B_Instruct.zip?rlkey=pw1ue4t4j85hogp3yf5yw9pig&dl=1",
        "md5sum": "6ca1682140cd8f91316a8b5b7dee6cd4",
    },
    "CodeLLaMA_13B_Instruct_fp32": {
        "url": "https://www.dropbox.com/scl/fi/gtor1fw1mmol8agqy178j/CodeLLaMA_13B_Instruct.zip?rlkey=0e9zh1cptwjb67yaez0aorou9&dl=1",
        "md5sum": "ebcb20dec3bd95a7e5a6eb93ed4c178d",
    },
    "opt_6.7B_fp32": {
        "url": "https://www.dropbox.com/scl/fi/mwy0uw51anodezy9rtcf1/OPT_6.7B.zip?rlkey=f8mtjg5eesuflrz3t5och4219&dl=1",
        "md5sum": "69cffdc090388ac2d2abcbe8163b0397",
    },
    "opt_1.3B_fp32": {
        "url": "https://www.dropbox.com/scl/fi/nyqvc8hejzo4mwnw4690w/OPT_1.3B.zip?rlkey=d1a11e9o8d6qmsisbdqo1qftl&dl=1",
        "md5sum": "a49490989fe030a0e9dee119285f7cf5",
    },
    "opt_125m_fp32": {
        "url": "https://www.dropbox.com/scl/fi/zvmdw8cdf7j0j3a99q8sx/OPT_125m.zip?rlkey=qehxgfs21m36wvm7ratwy1r5d&dl=1",
        "md5sum": "816958aed84120b763942ba83c1b010f",
    },
}

Qmodels = {
    "QM_ARM": {
        "LLaMA_7B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/92yg27e0p21izx7lalryb/LLaMA_7B.zip?rlkey=97m442isg29es3ddon66nwfmy&dl=1",  # noqa: E501
            "md5sum": "4118dca49c39547929d9e02d67838153",
        },
        "LLaMA2_7B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/1trpw92vmh4czvl28hkv0/LLaMA_7B_2_chat.zip?rlkey=dy1pdek0147gnuxdzpodi6pkt&dl=1",  # noqa: E501
            "md5sum": "af20c96de302c503a9fcfd5877ed0600",
        },
        "LLaMA2_13B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/rb7el1reycad98xrzif9a/LLaMA_13B_2_chat.zip?rlkey=wwd400no2uelcthvqxut3ojvj&dl=1",  # noqa: E501
            "md5sum": "f1f7693da630bb7aa269ecae5bcc397a",
        },
        "CodeLLaMA_7B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/m6qcwnsg37sdtewvh41sb/CodeLLaMA_7B_Instruct.zip?rlkey=mlnn1s76k63zez44uatmsc7ij&dl=1",
            "md5sum": "a5b4c15857944daaa1e1ee34c5917264",
        },
        "CodeLLaMA_13B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/7gcmtonyyyavdaeccnivi/CodeLLaMA_13B_Instruct.zip?rlkey=e1u6ne71prrtcjh1sp8hs5sns&dl=1",
            "md5sum": "d749ec83a54dcf40a7d87e7dbfba42d4",
        },
        "opt_125m_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/3dedmlzi36jngj74iskr6/OPT_125m.zip?rlkey=hy7z46cwfbr4dlz9bcs1mtx5b&dl=1",  # noqa: E501
            "md5sum": "2b42c3866c54642557046140367217fa",
        },
        "opt_1.3B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/1gzynks9u5j9bv5k2a0zj/OPT_1.3B.zip?rlkey=amtwlxypce84lvauo62on1601&dl=1",  # noqa: E501
            "md5sum": "1fb1296184c8c61e4066775ba59573b9",
        },
        "opt_6.7B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/7lu8rz8z5npe2nccfr66n/OPT_6.7B.zip?rlkey=5dtie29ncqscifs2g4ylpwnz7&dl=1",  # noqa: E501
            "md5sum": "6d061dc64ccc60864391f484b5e564d0",
        },
    },
    "QM_x86": {
        "LLaMA_7B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/i7yqzwr94wki2kywh9emr/LLaMA_7B.zip?rlkey=ce5j5p03wlwz5xdjrwuetxp4h&dl=1",  # noqa: E501
            "md5sum": "08c118ec34645808cd2d21678ad33659",
        },
        "LLaMA2_7B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/vu7wnes1c7gkcegg854ys/LLaMA_7B_2_chat.zip?rlkey=q61o8fpc954g1ke6g2eaot7cf&dl=1",  # noqa: E501
            "md5sum": "18f2193ccb393c7bca328f42427ef233",
        },
        "LLaMA2_13B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/t4u1jkp7gav8om4m6xjjv/LLaMA_13B_2_chat.zip?rlkey=tahltmq9bqu3ofx03r4mrsk2r&dl=1",  # noqa: E501
            "md5sum": "3684e5740f44ed05e213d6d807a1f136",
        },
        "CodeLLaMA_7B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/fav8kvwcuw1dpdiykny24/CodeLLaMA_7B_Instruct.zip?rlkey=bjhf467r8xb7di2lilqbgv8vm&dl=1",
            "md5sum": "b208eec1b1bbb6532f26b68a7a3caae6",
        },
        "CodeLLaMA_13B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/0appg7uacff9z21hth06n/CodeLLaMA_13B_Instruct.zip?rlkey=v6fxuomhqmskwqgtclsat9pzt&dl=1",
            "md5sum": "71ade74fe50b6beb378d52e19396926d",
        },
        "opt_125m_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/sl6kc1ql0877w550e4v17/OPT_125m.zip?rlkey=fsdqf3bc0vktl7iv6pfi6bbyx&dl=1",  # noqa: E501
            "md5sum": "c9c26bb5c8bf9867e21e525da744ef19",
        },
        "opt_1.3B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/t2t81kgskmpzzad985v72/OPT_1.3B.zip?rlkey=va6y8hqez7lxijdioigepjish&dl=1",  # noqa: E501
            "md5sum": "dd4801d7b65915a70a29d1d304ce5783",
        },
        "opt_6.7B_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/uj4z3kp5wd3cvaaiyppvs/OPT_6.7B.zip?rlkey=yw5dxd18ajsc20g3mr2rqvnnt&dl=1",  # noqa: E501
            "md5sum": "4aba1bee864029d06d1fec67f4d95a22",
        },
    },
    "QM_CUDA": {
        "LLaMA2_7B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/fwnd4x4t7065di0ojtbri/LLaMA_7B_2_chat.zip?rlkey=pzkux4yvjbsy8geua9wpio0gw&dl=1",  # noqa: E501
            "md5sum": "fedc72e60962128e3dbf070f770c5825",
        },
        "LLaMA2_13B_chat_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/k6j6gaeda5dk0ef56k272/LLaMA_13B_2_chat.zip?rlkey=fk2zvc5eqrmkm42xahhnqtf8o&dl=1",  # noqa: E501
            "md5sum": "24fd0af09f68d260b73594266ef1ee5d",
        },
        "CodeLLaMA_7B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/sejleaha7l257zmm7fbq9/CodeLLaMA_7B_Instruct.zip?rlkey=8pdyznt6wnr8gh4zr6h7ui6mf&dl=1",
            "md5sum": "c6bf03ddb47a7cbf1dc370fac8250c90",
        },
        "CodeLLaMA_13B_Instruct_awq_int4": {
            "url": "https://www.dropbox.com/scl/fi/1i2j3cnuh2posylhyi9xf/CodeLLaMA_13B_Instruct.zip?rlkey=689ltxudp3woat7ewigtrp5tt&dl=1",
            "md5sum": "3a9c5d2ed1863e686eba98221a618820",
        },
    },
    "INT8": {
        "opt_125m_smooth_int8": {
            "url": "https://www.dropbox.com/scl/fi/onoifsya2o96vb22mo0zq/OPT_125m.zip?rlkey=cuzmajx96v6nvfq3qctf3ke4u&dl=1",  # noqa: E501
            "md5sum": "e3bf0b7f13f393aa054de00a8433f232",
        },
        "opt_1.3B_smooth_int8": {
            "url": "https://www.dropbox.com/scl/fi/6a2lt28o37m0n5stpzj3q/OPT_1.3B.zip?rlkey=yzhj4pvo5y1dtvyh90ur0kotj&dl=1",  # noqa: E501
            "md5sum": "d40d797f32d7b8a0a8648e9395575b12",
        },
        "opt_6.7B_smooth_int8": {
            "url": "https://www.dropbox.com/scl/fi/jetyhj4rlhgsxz4qsizpc/OPT_6.7B.zip?rlkey=nuey04ta87hq80fupkduzsgjz&dl=1",  # noqa: E501
            "md5sum": "635994471bc6e56857cfa75f9949a090",
        },
    },
}


def _download_file(url, filepath):
    # Create a session
    with requests.Session() as session:
        session.headers = {"User-Agent": "Mozilla/5.0"}

        # Send a GET request to the URL
        response = session.get(url, stream=True)

        # Get the total file size
        file_size = int(response.headers.get("Content-Length", 0))

        # Check if the request was successful
        if response.status_code == 200:
            print(f"\nStart downloading the model to {filepath}.")
            # Download the file
            with open(filepath, "wb") as file:
                for chunk in tqdm(response.iter_content(chunk_size=1024), total=file_size // 1024, unit="KB"):
                    if chunk:
                        file.write(chunk)

            print(f"\nFile downloaded successfully: {filepath}")
        else:
            print(f"Failed to download the file. HTTP status code: {response.status_code}")


def _unzip_file(filepath, model_dir):
    print(f"Start unzip the model: {filepath}...")
    # Check if the file is a zip file
    if zipfile.is_zipfile(filepath):
        # Create a ZipFile object
        with zipfile.ZipFile(filepath, "r") as zip_ref:
            # Extract all the contents of the zip file in the current directory
            zip_ref.extractall(model_dir)
            print(f"File unzipped successfully: {filepath}")
    else:
        print(f"The file is not a zip file: {filepath}")


def _remove_file(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)
        print(f"File removed successfully: {filepath}")
    else:
        print(f"Error: {filepath} not a valid filename")


def _md5(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _main():
    parser = argparse.ArgumentParser(description="Download a file and check its md5sum")
    parser.add_argument("--model", help="The name of the file to download.")
    parser.add_argument("--QM", default="fp32", help="Quantization method.")

    args = parser.parse_args()

    if args.QM == "fp32":
        model_table = models
        model_dir = MODEL_DIR
    elif args.QM in Qmodels:
        model_table = Qmodels[args.QM]
        model_dir = "."
    else:
        raise NotImplementedError(f"{args.QM} is not supported.")

    if args.model in model_table:
        url = model_table[args.model]["url"]
        expected_md5sum = model_table[args.model]["md5sum"]

        filepath = f"{model_dir}/{args.model}.zip"  # Save the file in the current directory
        _download_file(url, filepath)

        actual_md5sum = _md5(filepath)

        if actual_md5sum == expected_md5sum:
            print("The md5sum of the file matches the expected md5sum.")
            _unzip_file(filepath, model_dir)  # Unzip the file
            _remove_file(filepath)  # Remove the zip file
        else:
            print(
                "The md5sum of the file does not match the expected md5sum.",
                f"Expected: {expected_md5sum}, got: {actual_md5sum}",
            )
    else:
        raise ValueError(f"Unexpected model: {args.model}. Supported options: {models.keys()}")


if __name__ == "__main__":
    _main()
