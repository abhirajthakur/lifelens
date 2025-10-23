import { useEffect } from "react";
import { useNavigate } from "react-router";

export default function Dashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate("/dashboard/upload", { replace: true });
  }, [navigate]);

  return null;
}
