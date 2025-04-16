import React, { useEffect, useState } from "react";
import {
  Typography,
  Container,
  Button,
  Box,
  TextField,
  List,
  ListItem,
  ListItemText,
  Divider
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";

import PageTracker from "../components/PageTracker";

function ProjectPage() {
  const { project_id } = useParams();
  const navigate = useNavigate();

  const [projectInfo, setProjectInfo] = useState();
  const [projectId, setProjectId] = useState();
  const [conversationList, setConversationList] = useState([]);
  const [filteredList, setFilteredList] = useState([]);

  const searchFor = valueToSearch => {
    const keysToSearch = [
      "model",
      "participant_id",
      "experiment_id",
      "conversation_id",
      "_id"
    ];

    const filtered = conversationList.filter(item =>
      keysToSearch.some(key =>
        item[key]?.toLowerCase().includes(valueToSearch.toLowerCase())
      )
    );
    setFilteredList(filtered);
  };

  const goToPage = conversation_id => {
    navigate(`/project/${project_id}/conversation/${conversation_id}`);
  };

  const downloadConverstionsJSON = filtered => {
    let listToJson = conversationList;
    let nameExtention = "";
    if (filtered) {
      listToJson = filteredList;
      nameExtention = "withFilter";
    }

    const json = JSON.stringify(listToJson, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `conversations-projectId_${projectId}-downloadDate_${new Date()}-${nameExtention}.json`;
    link.click();

    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const getProjectId = () => {
      setProjectId(project_id);
      listTheConversations(project_id);
      getProjectInfo(project_id);
    };

    const getProjectInfo = async local_project_id => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(
          `${backendURL}/dashboard/project/${local_project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        console.log("Projects:", data);
        setProjectInfo(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get project info.");
      }
    };

    const listTheConversations = async local_project_id => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(
          `${backendURL}/dashboard/conversations/${local_project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        console.log("Projects:", data);
        setConversationList(data);
        setFilteredList(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get the list.");
      }
    };

    getProjectId();
  }, [project_id]);

  return (
    <>
      <PageTracker
        arr={[
          {
            title: "Project",
            link: `/project/${projectId}`,
            idToShow: projectId
          }
        ]}
      />

      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          Project "{projectId}"
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          Creation date : {projectInfo?.created_at}
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          System Message
        </Typography>

        <Box
          component="pre"
          variant="body1"
          gutterBottom
          sx={{ p: 1, mt: 2, background: "#eee" }}
        >
          {projectInfo?.system_message}
        </Box>

        <Button
          variant="contained"
          sx={{ mt: 3, mb: 2, mr: 1 }}
          onClick={() => {
            navigate(`/systemmsg/${projectId}`);
          }}
        >
          Edit system message
        </Button>

        <Button
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          onClick={() => downloadConverstionsJSON(false)}
        >
          Download Convesations as JSON
        </Button>

        <hr />

        <div style={{ padding: 20 }}>
          <TextField
            label="Search by Model, Participant ID, Experiment ID, Conversation ID"
            variant="outlined"
            fullWidth
            onChange={e => searchFor(e.target.value)}
          />

          <Button
            variant="contained"
            sx={{ mt: 1, mb: 2 }}
            onClick={() => downloadConverstionsJSON(true)}
          >
            Download Filtered Convesations as JSON
          </Button>
        </div>

        <List
          sx={{
            p: 0,
            width: "100%",
            borderRadius: 2,
            border: "1px solid",
            borderColor: "divider",
            backgroundColor: "background.paper"
          }}
          aria-label="mailbox folders"
        >
          {filteredList.map((item, index) => {
            return (
              <div key={index}>
                <ListItem
                  sx={{
                    transition: "all 0.2s",
                    cursor: "pointer",
                    "&:hover": {
                      backgroundColor: "#eee"
                    }
                  }}
                  onClick={() => goToPage(item.conversation_id)}
                >
                  <ListItemText
                    primary={`${item.conversation_id} - ${
                      item.created_at.split(" ")[0]
                    } - ${item.model}`}
                  />
                </ListItem>
                <Divider component="li" />
              </div>
            );
          })}
        </List>
      </Container>
    </>
  );
}

export default ProjectPage;
