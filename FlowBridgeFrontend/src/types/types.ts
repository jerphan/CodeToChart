export interface sourceFile{
    fileID : string;
    fileName : string;
    filePath : string;
    fileContent : string;
}

export interface pyProject{
    projectID : string;
    projectName : string;
    files : sourceFile[];
}

export interface errorDetail{
    code : string;
    message : string;
    filePath : string;
}

export interface errorResponse{
    error : errorDetail;
}

export type uploadStatus = "idle" | "uploading" | "success" | "error";