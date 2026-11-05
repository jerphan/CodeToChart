import {useState, useEffect} from "react";
import "../App.css";
import {pyProject, sourceFile} from "../types/types";

export interface projectViewerProperties{
    //Keeps track of the currently uploaded pyProject object
    project : pyProject | null;
    //If the user selects a specific file then we swap the view to that file
    onSelectFile? : (file : sourceFile) => void;
}

interface sourceFileCardProperties{
    file : sourceFile;
}

export default function ProjectViewer({project, onSelectFile} : projectViewerProperties){
    const [selectedFileID, setSelectedFileID] = useState<string | null>(null)
    
    useEffect(() => {
        //Automatically select the first file in the pyProject object to view
        if(project && project.files.length > 0){
            const firstFile = project.files[0];
            setSelectedFileID(firstFile.fileID);
            onSelectFile?.(firstFile);
        }
        //Otherwise set the selected fileID as null
        else{
            setSelectedFileID(null)
        }
    }, [project]);

    const activeFile = project?.files.find((file) => file.fileID === selectedFileID) || null;

    //When a file is clicked, then set it to the currently active file
    const handleFileClicked = (file : sourceFile) => {
        setSelectedFileID(file.fileID);
        onSelectFile?.(file);
    };


}