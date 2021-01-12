import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Menu,
  MenuItem,
  TextField
} from "@material-ui/core";
import { GetProjectList_projects } from "./__generated__/GetProjectList";
import { useApolloClient, useMutation } from "@apollo/client";
import MoreVertIcon from "@material-ui/icons/MoreVert";
import React, { ReactElement } from "react";
import gql from "graphql-tag";

const DELETE_PROJECT_MUTATION = gql`
  mutation DeleteProject($id: ID!) {
    deleteProject(id: $id) {
      id
    }
  }
`;

export default function ProjectMenu(props: { project: GetProjectList_projects }): ReactElement {
  const [anchorEl, setAnchorEl] = React.useState<Element | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <IconButton onClick={handleClick}>
        <MoreVertIcon />
      </IconButton>
      <Menu id="simple-menu" anchorEl={anchorEl} keepMounted open={Boolean(anchorEl)} onClose={handleClose}>
        <MenuItem onClick={handleClose}>
          <RemoveProjectDialogButton project={props.project} />
        </MenuItem>
      </Menu>
    </>
  );
}

function RemoveProjectDialogButton(props: { project: GetProjectList_projects }): ReactElement {
  const [open, setOpen] = React.useState<boolean>(false);
  const [confirmation, setConfirmation] = React.useState<string>("");
  const [deleteProject] = useMutation(DELETE_PROJECT_MUTATION);
  const apolloClient = useApolloClient();

  const handleClickOpen = () => {
    setOpen(true);
  };
  const handleClose = () => {
    setOpen(false);
  };
  const handleDelete = () => {
    if (confirmation === props.project.name) {
      deleteProject({ variables: { id: props.project.id } }).then(() => {
        apolloClient.resetStore();
      });
      handleClose();
    }
  };

  return (
    <>
      <Button onClick={handleClickOpen}>Delete Project</Button>
      <Dialog onClose={handleClose} open={open}>
        <DialogTitle>Confirm Project Deletion</DialogTitle>
        <DialogContent dividers>
          <p> Please confirm project deletion by typing &ldquo;{props.project.name}&rdquo; </p>
          <TextField onChange={(event) => setConfirmation(event.target.value)} autoFocus margin="dense" fullWidth />
        </DialogContent>
        <DialogActions>
          <Button autoFocus onClick={handleClose}>
            Cancel
          </Button>
          <Button autoFocus onClick={handleDelete} color="primary">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}