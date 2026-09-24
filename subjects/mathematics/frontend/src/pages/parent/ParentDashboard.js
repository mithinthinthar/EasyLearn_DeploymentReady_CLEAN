import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tooltip,
  IconButton,
} from "@mui/material";
import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
import { logUserActivity } from "../../utils/logger";
import CustomToast from "../../components/CustomToast";

import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import PersonAddAltOutlinedIcon from "@mui/icons-material/PersonAddAltOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

const ParentDashboard = () => {
  const { t } = useLanguage();
  const user = JSON.parse(localStorage.getItem("user")) || {};
  const navigate = useNavigate();

  const [studentCode, setStudentCode] = useState("");
  const [nickname, setNickname] = useState("");
  const [children, setChildren] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [openUnlinkDialog, setOpenUnlinkDialog] = useState(false);
  const [selectedChildToUnlink, setSelectedChildToUnlink] = useState(null);

  const [toast, setToast] = useState({
    open: false,
    type: "info",
    title: "",
    message: "",
  });

  const showToast = (type, title, message) => {
    setToast({
      open: true,
      type,
      title,
      message,
    });
  };

  const fetchChildren = async () => {
    try {
      setIsLoading(true);

      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/parent/children`
      );
      const data = await response.json();

      if (data.success) {
        setChildren(data.children || []);
      } else {
        showToast(
          "error",
          t("parent_toast_error_title"),
          data.message || t("parent_toast_load_children_failed")
        );
      }
    } catch (error) {
      console.error("Failed to fetch linked children:", error);
      showToast(
        "error",
        t("parent_toast_error_title"),
        t("parent_toast_load_children_failed")
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    logUserActivity("viewed_parent_dashboard");
    fetchChildren();
  }, []);

  const handleLinkChild = async () => {
    if (!studentCode.trim()) {
      showToast(
        "error",
        t("parent_toast_error_title"),
        t("parent_toast_enter_student_code")
      );
      return;
    }

    try {
      setIsSubmitting(true);

      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/parent/children/link`,
        {
          method: "POST",
          body: JSON.stringify({
            student_code: studentCode.trim(),
            nickname: nickname.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!data.success) {
        showToast(
          "error",
          t("parent_toast_error_title"),
          data.message || t("parent_toast_link_failed")
        );
        return;
      }

      setStudentCode("");
      setNickname("");

      showToast(
        "success",
        t("parent_toast_success_title"),
        data.message || t("parent_toast_link_success")
      );

      fetchChildren();
    } catch (error) {
      console.error("Failed to link child:", error);
      showToast(
        "error",
        t("parent_toast_error_title"),
        t("parent_toast_link_failed")
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestUnlinkChild = (child) => {
    setSelectedChildToUnlink(child);
    setOpenUnlinkDialog(true);
  };

  const handleCloseUnlinkDialog = () => {
    setOpenUnlinkDialog(false);
    setSelectedChildToUnlink(null);
  };

  const handleUnlinkChild = async () => {
    if (!selectedChildToUnlink) return;

    try {
      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/parent/children/${selectedChildToUnlink.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!data.success) {
        showToast(
          "error",
          t("parent_toast_error_title"),
          data.message || t("parent_toast_unlink_failed")
        );
        return;
      }

      showToast(
        "success",
        t("parent_toast_success_title"),
        data.message || t("parent_toast_unlink_success")
      );

      setChildren((prev) =>
        prev.filter((child) => child.id !== selectedChildToUnlink.id)
      );

      handleCloseUnlinkDialog();
    } catch (error) {
      console.error("Failed to unlink child:", error);
      showToast(
        "error",
        t("parent_toast_error_title"),
        t("parent_toast_unlink_failed")
      );
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      <Box mb={3}>
        <Typography variant="h4" fontWeight="bold" color="#111827" gutterBottom>
          {t("parent_home_title")}
        </Typography>
        <Typography color="text.secondary">
          {t("parent_home_subtitle")}
        </Typography>
      </Box>

      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          borderRadius: "24px",
          border: "1px solid #E5E7EB",
          background: "linear-gradient(135deg, #EEF2FF 0%, #F8FAFF 100%)",
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            gap: 2,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <Box>
            <Typography variant="h6" fontWeight="bold" color="#111827">
              {t("parent_welcome_back")}, {user?.name || "Parent"}
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 0.5 }}>
              {t("parent_manage_text")}
            </Typography>
          </Box>

          <Chip
            icon={<PeopleAltOutlinedIcon />}
            label={`${t("parent_total_linked_children")}: ${children.length}`}
            sx={{
              bgcolor: "#ffffff",
              border: "1px solid #E5E7EB",
              fontWeight: "bold",
            }}
          />
        </Box>
      </Paper>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "370px 1fr" },
          gap: 3,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, sm: 3 },
            borderRadius: "22px",
            border: "1px solid #E5E7EB",
            height: "fit-content",
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
            <PersonAddAltOutlinedIcon sx={{ color: "#3855c0" }} />
            <Typography variant="h6" fontWeight="bold">
              {t("parent_link_child_title")}
            </Typography>
          </Box>

          <Stack spacing={2}>
            <TextField
              label={t("parent_student_code")}
              value={studentCode}
              onChange={(e) => setStudentCode(e.target.value)}
              fullWidth
            />

            <TextField
              label={t("parent_nickname_optional")}
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              fullWidth
            />

            <Button
              variant="contained"
              onClick={handleLinkChild}
              disabled={isSubmitting}
              sx={{
                py: 1.4,
                borderRadius: "14px",
                textTransform: "none",
                fontWeight: "bold",
                bgcolor: "#3855c0",
                "&:hover": { bgcolor: "#2d4499" },
              }}
            >
              {isSubmitting ? (
                <CircularProgress size={22} color="inherit" />
              ) : (
                t("parent_link_child_button")
              )}
            </Button>
          </Stack>
        </Paper>

        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, sm: 3 },
            borderRadius: "22px",
            border: "1px solid #E5E7EB",
            height: "fit-content",
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          <Typography variant="h6" fontWeight="bold" mb={2}>
            {t("parent_linked_children_title")}
          </Typography>

          {isLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
              <CircularProgress />
            </Box>
          ) : children.length === 0 ? (
            <Typography color="text.secondary">
              {t("parent_no_children")}
            </Typography>
          ) : (
            <Stack spacing={2}>
              {children.map((child) => (
                <Paper
                  key={child.id}
                  elevation={0}
                  sx={{
                    p: { xs: 2, sm: 2.5 },
                    borderRadius: "18px",
                    border: "1px solid #E5E7EB",
                    bgcolor: "#FFFFFF",
                    minWidth: 0,
                    overflow: "hidden",
                    transition: "0.2s ease",
                    "&:hover": {
                      boxShadow: "0 10px 24px rgba(15, 23, 42, 0.06)",
                    },
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: { xs: "flex-start", sm: "center" },
                      gap: 2,
                      flexWrap: "wrap",
                      minWidth: 0,
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: { xs: "flex-start", sm: "center" },
                        gap: 2,
                        minWidth: 0,
                        flex: "1 1 260px",
                        width: { xs: "100%", sm: "auto" },
                      }}
                    >
                      <Avatar
                        src={child.photo_url || ""}
                        alt={child.name || "Student"}
                        sx={{
                          width: 52,
                          height: 52,
                          bgcolor: "#E0E7FF",
                          color: "#3855c0",
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {!child.photo_url && (child?.name?.[0]?.toUpperCase() || "S")}
                      </Avatar>

                      <Box sx={{ minWidth: 0, flex: 1 }}>
                        <Typography
                          fontWeight="bold"
                          color="#111827"
                          sx={{
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: { xs: "normal", sm: "nowrap" },
                            wordBreak: "break-word",
                            lineHeight: 1.25,
                          }}
                        >
                          {child.nickname ? `${child.nickname} (${child.name})` : child.name}
                        </Typography>

                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: { xs: "normal", sm: "nowrap" },
                            wordBreak: "break-all",
                            maxWidth: "100%",
                            lineHeight: 1.35,
                            mt: 0.3,
                          }}
                        >
                          {child.email}
                        </Typography>

                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mt: 0.8,
                            minWidth: 0,
                          }}
                        >
                          <BadgeOutlinedIcon sx={{ fontSize: 16, color: "#6B7280", flexShrink: 0 }} />
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              minWidth: 0,
                            }}
                          >
                            {t("parent_student_id")}: {child.student_code}
                          </Typography>
                        </Box>

                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ display: "block", mt: 0.6 }}
                        >
                          {t("parent_linked_on")}:{" "}
                          {new Date(child.linked_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </Box>

                    <Box
                      sx={{
                        display: "flex",
                        gap: 1,
                        flexWrap: "wrap",
                        width: { xs: "100%", sm: "auto" },
                        justifyContent: { xs: "flex-start", sm: "flex-end" },
                        flexShrink: 0,
                      }}
                    >
                      <Button
                        variant="outlined"
                        startIcon={<VisibilityOutlinedIcon />}
                        onClick={() => navigate(`/parentDashboard/child/${child.id}`)}
                        sx={{
                          borderRadius: "12px",
                          textTransform: "none",
                          fontWeight: "bold",
                          minWidth: { xs: 0, sm: 130 },
                          flex: { xs: "1 1 auto", sm: "0 0 auto" },
                          maxWidth: { xs: 180, sm: "none" },
                        }}
                      >
                        {t("parent_view_dashboard")}
                      </Button>

                      <Tooltip title={t("parent_unlink")} arrow>
                        <IconButton
                          onClick={() => handleRequestUnlinkChild(child)}
                          sx={{
                            width: 42,
                            height: 42,
                            border: "1px solid #FECACA",
                            color: "#DC2626",
                            borderRadius: "12px",
                            flexShrink: 0,
                            "&:hover": {
                              bgcolor: "#FEF2F2",
                              borderColor: "#FCA5A5",
                            },
                          }}
                        >
                          <DeleteOutlineIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Stack>
          )}
        </Paper>
      </Box>
      <Dialog
        open={openUnlinkDialog}
        onClose={handleCloseUnlinkDialog}
        PaperProps={{
          sx: {
            borderRadius: "18px",
            px: 1,
            py: 1,
            width: "100%",
            maxWidth: 420,
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: "bold", color: "#111827" }}>
          {t("parent_unlink_dialog_title")}
        </DialogTitle>

        <DialogContent>
          <DialogContentText sx={{ color: "#4B5563" }}>
            {selectedChildToUnlink
              ? t("parent_unlink_dialog_desc").replace(
                  "{name}",
                  selectedChildToUnlink.nickname
                    ? `${selectedChildToUnlink.nickname} (${selectedChildToUnlink.name})`
                    : selectedChildToUnlink.name
                )
              : t("parent_unlink_dialog_desc_fallback")}
          </DialogContentText>
        </DialogContent>

        <DialogActions sx={{ px: 2, pb: 2 }}>
          <Button
            onClick={handleCloseUnlinkDialog}
            sx={{
              textTransform: "none",
              fontWeight: 700,
              color: "#6B7280",
            }}
          >
            {t("parent_unlink_dialog_cancel")}
          </Button>

          <Button
            onClick={handleUnlinkChild}
            variant="contained"
            disableElevation
            sx={{
              textTransform: "none",
              fontWeight: 700,
              borderRadius: "10px",
              bgcolor: "#c03838",
              "&:hover": {
                bgcolor: "#992d2d",
              },
            }}
          >
            {t("parent_unlink_dialog_confirm")}
          </Button>
        </DialogActions>
      </Dialog>
      <CustomToast
        open={toast.open}
        type={toast.type}
        title={toast.title}
        message={toast.message}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
      />
    </Box>
  );
};

export default ParentDashboard;