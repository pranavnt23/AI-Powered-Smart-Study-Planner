import api from "@/lib/axios";

export async function uploadDocument(file: File) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(
      "/upload/",
      formData
    );

    const result = response.data;
    const uploadData = result?.data ?? result;

    return uploadData?.data ?? uploadData;
  } catch (error) {
    console.error(error);
    return {
      status: false,
      message: "Upload failed",
    };
  }
}