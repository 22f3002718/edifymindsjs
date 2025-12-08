import React, { useState, useRef } from "react";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Upload, File, X, Loader2 } from "lucide-react";

const FileUpload = ({ onUploadSuccess, className = "" }) => {
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
  const ALLOWED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.zip'
  ];

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File size must be less than 5MB. Your file is ${formatFileSize(file.size)}`);
      return;
    }

    // Validate file extension
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
      toast.error(`File type ${fileExt} is not allowed. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error("Please select a file first");
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success(`File uploaded successfully: ${selectedFile.name}`);
      
      // Call parent callback with upload result
      if (onUploadSuccess) {
        onUploadSuccess({
          url: response.data.url,
          filename: response.data.filename,
          size: response.data.size
        });
      }

      // Reset state
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error("Upload error:", error);
      const errorMsg = error.response?.data?.detail || "Failed to upload file";
      toast.error(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-purple-400 transition-colors">
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3 bg-purple-50 rounded-full">
            <Upload className="h-6 w-6 text-purple-600" />
          </div>
          
          <div className="text-center">
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="text-sm font-medium text-purple-600 hover:text-purple-700">
                Choose a file
              </span>
              <input
                id="file-upload"
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileSelect}
                disabled={uploading}
                accept={ALLOWED_EXTENSIONS.join(',')}
              />
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Max 5MB • Documents, Images, Archives
            </p>
          </div>

          {selectedFile && (
            <div className="w-full mt-3 p-3 bg-gray-50 rounded-md flex items-center justify-between">
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                <File className="h-5 w-5 text-gray-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              {!uploading && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveFile}
                  className="flex-shrink-0 ml-2"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedFile && (
        <Button
          type="button"
          onClick={handleUpload}
          disabled={uploading}
          className="w-full text-white"
          style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
        >
          {uploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Upload File
            </>
          )}
        </Button>
      )}
    </div>
  );
};

export default FileUpload;
