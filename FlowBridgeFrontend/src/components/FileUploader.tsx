import {ChangeEvent, useState, useEffect, useRef} from 'react';
import "../App.css";
import axios, {AxiosError} from 'axios';
import {errorResponse, pyProject, uploadStatus} from "../types/types"

const api = axios.create({
    baseURL: "http://localhost:8000"
})

export interface fileUploaderProperties{
    onProjectLoaded: (project: pyProject) => void;
    projectName?: string;
}

export default function FileUploader({onProjectLoaded, projectName=""}: fileUploaderProperties){
    //Setting the constants for the full project and then the selectedFile to display later
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [pyProjectName, setPyProjectName] = useState<string>(projectName)
    //Setting default state for the status of a file upload
    const [status, setStatus] = useState<uploadStatus>("idle");
    //Constants for errors, or error codes. They both can either be strings or null if there is no error
    const [error, setError] = useState<string | null>(null);
    const[errorCode, setErrorCode] = useState<string | null>(null);
    //The controller will cancel the request if needed. If not needed then it will be Null type
    const controllerRef = useRef<AbortController | null>(null);
    //Constant to keep reference of the file input. Will be null if nothing is uploaded
    const fileInputReference = useRef<HTMLInputElement | null>(null);

    useEffect(()=> {
        return () => {
            controllerRef.current?.abort();
        }
    }, []);

    //Creating a FormData object to send to the backend
    const buildFormData = (fileUpload: File): FormData =>{
        const formData = new FormData();
        //Add in the file uploaded
        formData.append("file", fileUpload)
        //Add in the project's name
        if(projectName.trim()){
            formData.append("pyProjectName", projectName.trim());
        }
        return formData;
    }

    const handleUploadError = (error : unknown) => {
        //If the axios detects that a caught error was cancelled, then we just set the state back to idle
        if(axios.isCancel(error)){
            setStatus("idle")
            return;
        }
        //Otherwise we set the status of the upload to error
        setStatus("error")
        const axiosErr = error as AxiosError<errorResponse>
    };

    const handleSingleFile = async (fileUpload : File)=> {
        controllerRef.current?.abort();
        const controller = new AbortController();
        controllerRef.current = controller;

        //Set the useStates to the appropriate states before beginning the upload logic
        setStatus("uploading")
        setError(null);
        setErrorCode(null);

        try{
            const formData = buildFormData(fileUpload);
            const response = await api.post<pyProject>("/api/projects/file", formData,{
                signal : controller.signal,
            });
            //If the controller did not abort, then the response was a success
            setStatus("success")
            onProjectLoaded(response.data);
        }
        catch(err){
            handleUploadError(err);
        }
    };

    const handleZipFile = async (fileUpload : File)=> {
        controllerRef.current?.abort();
        const controller = new AbortController();
        controllerRef.current = controller;
        
        //Set the useStates to the appropriate states before beginning the upload logic
        setStatus("uploading")
        setError(null);
        setErrorCode(null);

        try{
            const formData = buildFormData(fileUpload);
            const response = await api.post<pyProject>("/api/projects/zip", formData,{
                signal : controller.signal,
            });
            //If the controller did not abort, then the response was a success
            setStatus("success")
            onProjectLoaded(response.data);
        }
        catch(err){
            handleUploadError(err);
        }
    };

    const uploadFileByType = async (fileUpload : File) => {
        //Change the casing of the file name to lower case.
        const lowerName = fileUpload.name.toLowerCase();
        //If the file name ends with .py then it is a single file
        if(lowerName.endsWith(".py")){
            await handleSingleFile(fileUpload)
        }
        //If the file name ends with .zip then it is a zip file
        else if(lowerName.endsWith(".zip")){
            await handleZipFile(fileUpload);
        }
        //If it is neither of the above, we do not support the file type and should reject the upload
        else{
            setStatus("error");
            setErrorCode("UNSUPPORTED_INPUT")
            setError("Upload must be a single python file or a zip file")
        }
    };

    const handleFileChange = async (e:ChangeEvent<HTMLInputElement>) =>{
        const files = e.target.files;
        //If the user clicks on the button but then does not upload anything then we do nothing
        if(!files || files.length === 0){
            return;
        }
        //The default selected file will be the first one
        const selectedFile = files[0]
        setSelectedFile(selectedFile)
        await uploadFileByType(selectedFile);
        //Next we reset the input value so that clicking the file upload button still triggers a ChangeEvent
        if (fileInputReference.current){
            fileInputReference.current.value = "";
        }
    };

    return (
        <>
            <label htmlFor="fileUpload">
                <img src="UploadFileButton.png" alt="Upload Icon" className = "toolIcon"/>
            </label>
            <input type="file" id="fileUpload" className = "toolButton" onChange={handleFileChange}></input>
        </>
    );
}