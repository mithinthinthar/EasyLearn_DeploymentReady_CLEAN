export const LOCAL_MODE = process.env.REACT_APP_LOCAL_MODE === "true";

export const LOCAL_GUEST_USER = {
  id: 17766,
  name: "Local Student",
  email: "local.student@easylearn.test",
  role: "student",
  language: "english",
  local_mode: true,
};

export const ensureLocalGuestUser = () => {
  if (!LOCAL_MODE) return null;

  try {
    const storedUser = JSON.parse(localStorage.getItem("user"));
    if (storedUser?.id && storedUser?.role === "student") {
      return storedUser;
    }
  } catch (error) {
    console.warn("The saved local user was invalid and has been reset.", error);
  }

  const guestUser = { ...LOCAL_GUEST_USER };
  localStorage.setItem("user", JSON.stringify(guestUser));
  return guestUser;
};

