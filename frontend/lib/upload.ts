import api from "@/lib/axios";

export async function uploadDocument(file: File) {

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(
      "/upload/",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
    
  } catch (error) {
    console.error(error);
    return {
      status: false,
      message: "Upload failed",
    };
  }
}