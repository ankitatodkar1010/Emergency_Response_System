import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

const EVENT_LABELS = {
  incident_created: "INCIDENT CREATED",
  incident_updated: "INCIDENT UPDATED",
  responder_assigned: "RESPONDER ASSIGNED",
  assignment_status_updated: "ASSIGNMENT STATUS",
  assignment_reassigned: "ASSIGNMENT REASSIGNED",
  new_incident: "NEW INCIDENT",
};

const EVENT_ICONS = {
  incident_created: "🚨",
  incident_updated: "↻",
  responder_assigned: "🚑",
  assignment_status_updated: "✓",
  assignment_reassigned: "⇄",
  new_incident: "⚡",
};

function App() {
  /* =========================
     AUTH STATE
  ========================= */

  const [token, setToken] = useState(
    () => localStorage.getItem("access_token") || ""
  );

  const [authMode, setAuthMode] = useState("login");

  const [loginData, setLoginData] = useState({
    email: "",
    password: "",
  });

  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
  });

  /* =========================
     INCIDENT STATE
  ========================= */

  const [emergencyType, setEmergencyType] = useState(
    "Medical Emergency"
  );

  const [severity, setSeverity] = useState(3);
  const [peopleAffected, setPeopleAffected] = useState(1);
  const [peopleTrapped, setPeopleTrapped] = useState(0);
  const [escalating, setEscalating] = useState(false);

  const [incident, setIncident] = useState(null);
  const [status, setStatus] = useState("");

  /* =========================
     LOCATION STATE
  ========================= */

  const [location, setLocation] = useState(null);

  const [locationStatus, setLocationStatus] = useState(
    "Detecting location..."
  );

  /* =========================
     WEBSOCKET STATE
  ========================= */

  const [wsStatus, setWsStatus] = useState("DISCONNECTED");

  const wsRef = useRef(null);
  const incidentIdRef = useRef(null);

  /* =========================
     REAL-TIME EVENT FEED
  ========================= */

  const [events, setEvents] = useState([]);

  /* =========================
     ERROR STATE
  ========================= */

  const [error, setError] = useState("");

  /* =========================
     AUTH HELPERS
  ========================= */

  const saveToken = (newToken) => {
    localStorage.setItem("access_token", newToken);
    setToken(newToken);
  };

  const handleAuthError = (message) => {
    setError(message || "Something went wrong.");
  };

  /* =========================
     EVENT FEED HELPERS
  ========================= */

  const addEvent = (eventType, data = {}) => {
    const now = new Date();

    const event = {
      id: `${Date.now()}-${Math.random()}`,
      type: eventType,
      data,
      time: now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }),
    };

    setEvents((previous) => [event, ...previous].slice(0, 30));
  };

  const getEventDetails = (event) => {
    const data = event.data || {};

    switch (event.type) {
      case "incident_created":
        if (data.incident_id) {
          return `Incident #${data.incident_id} created`;
        }

        if (data.id) {
          return `Incident #${data.id} created`;
        }

        if (data.incident_type) {
          return `${data.incident_type} incident created`;
        }

        return "New emergency incident created";

      case "incident_updated":
        if (data.incident_id) {
          return `Incident #${data.incident_id} updated`;
        }

        if (data.id) {
          return `Incident #${data.id} updated`;
        }

        return "Incident information updated";

      case "responder_assigned":
        if (data.responder_id) {
          return `Responder #${data.responder_id} assigned`;
        }

        if (data.assignment_id) {
          return `Assignment #${data.assignment_id} created`;
        }

        return "Responder assigned to incident";

      case "assignment_status_updated":
        if (data.status) {
          return `Assignment status → ${String(
            data.status
          ).replaceAll("_", " ")}`;
        }

        return "Assignment status updated";

      case "assignment_reassigned":
        if (data.responder_id) {
          return `Reassigned to responder #${data.responder_id}`;
        }

        return "Incident reassigned to another responder";

      case "new_incident":
        if (data.incident_id) {
          return `New incident #${data.incident_id} received`;
        }

        return "New emergency received";

      default:
        return "Real-time system event received";
    }
  };

  const extractIncident = (data) => {
    if (!data || typeof data !== "object") {
      return null;
    }

    if (
      data.incident &&
      typeof data.incident === "object"
    ) {
      return data.incident;
    }

    return data;
  };

  /* =========================
     LOGIN
  ========================= */

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setStatus("");

    try {
      const formData = new URLSearchParams();

      formData.append("username", loginData.email);
      formData.append("password", loginData.password);

      const response = await fetch(
        `${API_URL}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Login failed."
        );
      }

      saveToken(data.access_token);
      setStatus("Authenticated");
    } catch (err) {
      handleAuthError(err.message);
    }
  };

  /* =========================
     REGISTER
  ========================= */

  const handleRegister = async (event) => {
    event.preventDefault();

    setError("");
    setStatus("");

    try {
      const response = await fetch(
        `${API_URL}/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: registerData.name,
            email: registerData.email,
            password: registerData.password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Registration failed."
        );
      }

      const formData = new URLSearchParams();

      formData.append(
        "username",
        registerData.email
      );

      formData.append(
        "password",
        registerData.password
      );

      const loginResponse = await fetch(
        `${API_URL}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: formData,
        }
      );

      const loginResult =
        await loginResponse.json();

      if (!loginResponse.ok) {
        throw new Error(
          loginResult.detail ||
            "Registration succeeded, but login failed."
        );
      }

      saveToken(loginResult.access_token);

      setStatus("Account created");

      setRegisterData({
        name: "",
        email: "",
        password: "",
      });
    } catch (err) {
      handleAuthError(err.message);
    }
  };

  /* =========================
     LOCATION
  ========================= */

  useEffect(() => {
    if (!token) {
      return;
    }

    if (!navigator.geolocation) {
      setLocationStatus("GPS unavailable");
      return;
    }

    setLocationStatus("Detecting location...");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };

        setLocation(coords);
        setLocationStatus("Location detected");
      },
      (geoError) => {
        console.error(
          "Geolocation error:",
          geoError
        );

        setLocation(null);

        if (geoError.code === 1) {
          setLocationStatus(
            "Location permission denied"
          );
        } else if (geoError.code === 2) {
          setLocationStatus(
            "Location unavailable"
          );
        } else if (geoError.code === 3) {
          setLocationStatus(
            "Location request timed out"
          );
        } else {
          setLocationStatus(
            "Unable to detect location"
          );
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  }, [token]);

  /* =========================
     WEBSOCKET
  ========================= */

  useEffect(() => {
    if (!token) {
      return;
    }

    let reconnectTimer = null;
    let manuallyClosed = false;

    const connectWebSocket = () => {
      if (manuallyClosed) {
        return;
      }

      setWsStatus("CONNECTING");

      const ws = new WebSocket(
        `ws://localhost:8000/ws?token=${encodeURIComponent(
          token
        )}`
      );

      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus("LIVE");

        addEvent("system", {
          message:
            "Real-time connection established",
        });
      };

      ws.onmessage = (message) => {
        try {
          const parsed = JSON.parse(
            message.data
          );

          const eventType =
            parsed.event ||
            parsed.event_type ||
            parsed.type ||
            parsed.name;

          if (!eventType) {
            addEvent("system", parsed);
            return;
          }

          addEvent(eventType, parsed);

          const incidentData =
            extractIncident(parsed);

          /*
           * IMPORTANT:
           *
           * Do not allow events belonging to
           * another incident to overwrite the
           * current active incident.
           */

          const receivedIncidentId =
            parsed.incident_id ||
            parsed.incident?.id ||
            parsed.id;

          const currentIncidentId =
            incidentIdRef.current;

          const eventBelongsToCurrentIncident =
            currentIncidentId &&
            receivedIncidentId &&
            Number(receivedIncidentId) ===
              Number(currentIncidentId);

          /*
           * INCIDENT CREATED
           *
           * If we don't have an active incident yet,
           * allow the event to initialize it.
           */

          if (
            eventType === "incident_created" &&
            incidentData
          ) {
            if (!currentIncidentId) {
              const newIncidentId =
                incidentData.id ||
                incidentData.incident_id;

              if (newIncidentId) {
                incidentIdRef.current =
                  newIncidentId;
              }

              setIncident(incidentData);
            } else if (
              eventBelongsToCurrentIncident
            ) {
              setIncident((previous) => ({
                ...previous,
                ...incidentData,
              }));
            }
          }

          /*
           * INCIDENT UPDATED
           */

          if (
            eventType === "incident_updated" &&
            eventBelongsToCurrentIncident
          ) {
            setIncident((previous) => ({
              ...previous,
              ...incidentData,
            }));
          }

          /*
           * ASSIGNMENT EVENTS
           *
           * Only update the active incident when
           * the event belongs to that incident.
           */

          if (
            [
              "responder_assigned",
              "assignment_status_updated",
              "assignment_reassigned",
            ].includes(eventType) &&
            eventBelongsToCurrentIncident
          ) {
            setIncident((previous) => ({
              ...previous,
              ...incidentData,
            }));
          }

          if (
            eventType ===
            "assignment_status_updated"
          ) {
            if (
              eventBelongsToCurrentIncident &&
              parsed.status
            ) {
              setStatus(
                String(parsed.status)
                  .replaceAll("_", " ")
                  .toUpperCase()
              );
            }
          }

          if (
            eventType === "responder_assigned" &&
            eventBelongsToCurrentIncident
          ) {
            setStatus(
              "RESPONDER ASSIGNED"
            );
          }

          if (
            eventType ===
            "assignment_reassigned" &&
            eventBelongsToCurrentIncident
          ) {
            setStatus(
              "RESPONDER REASSIGNED"
            );
          }

        } catch (err) {
          console.error(
            "WebSocket message parsing error:",
            err
          );

          addEvent("system", {
            message: message.data,
          });
        }
      };

      ws.onerror = (wsError) => {
        console.error(
          "WebSocket error:",
          wsError
        );

        setWsStatus("ERROR");
      };

      ws.onclose = () => {
        wsRef.current = null;

        if (manuallyClosed) {
          setWsStatus("DISCONNECTED");
          return;
        }

        setWsStatus("RECONNECTING");

        reconnectTimer = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      };
    };

    connectWebSocket();

    return () => {
      manuallyClosed = true;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      setWsStatus("DISCONNECTED");
    };
  }, [token]);

  /* =========================
     CREATE INCIDENT
  ========================= */

  const handleSendAlert = async () => {
    if (!location) {
      setError(
        "Location is required before sending an emergency alert."
      );

      return;
    }

    if (peopleTrapped > peopleAffected) {
      setError(
        "People trapped cannot be greater than people affected."
      );

      return;
    }

    setError("");
    setStatus("CREATING INCIDENT");

    try {
      const response = await fetch(
        `${API_URL}/incidents`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            incident_type: emergencyType,
            description: `${emergencyType} emergency reported by user`,
            severity: Number(severity),
            people_affected:
              Number(peopleAffected),
            people_trapped:
              Number(peopleTrapped),
            escalating: escalating,
            latitude: location.latitude,
            longitude: location.longitude,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to create incident."
        );
      }

      /*
       * Backend response is the source of truth.
       *
       * This response should contain:
       * risk_score
       * priority
       * priority_reason
       */

      setIncident(data);

      const createdIncidentId =
        data.id || data.incident_id;

      if (createdIncidentId) {
        incidentIdRef.current =
          createdIncidentId;
      }

      setStatus("INCIDENT CREATED");

    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  };

  /* =========================
     LOGOUT
  ========================= */

  const handleLogout = () => {
    localStorage.removeItem(
      "access_token"
    );

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setToken("");
    setIncident(null);
    setEvents([]);

    setEmergencyType(
      "Medical Emergency"
    );

    setSeverity(3);
    setPeopleAffected(1);
    setPeopleTrapped(0);
    setEscalating(false);

    setStatus("");
    setError("");

    setLocation(null);
    setLocationStatus(
      "Location unavailable"
    );

    setWsStatus("DISCONNECTED");

    incidentIdRef.current = null;
  };

  /* =========================
     AUTH SCREEN
  ========================= */

  if (!token) {
    return (
      <div className="auth-app">
        <div className="auth-shell">

          <div className="auth-brand">
            <div className="brand-mark">
              🚨
            </div>

            <div>
              <div className="brand-name">
                RESPONSECORE
              </div>

              <div className="brand-subtitle">
                Emergency Response &
                Coordination
              </div>
            </div>
          </div>

          <div className="auth-card">

            <div className="auth-card-header">

              <span className="eyebrow">
                {authMode === "login"
                  ? "SECURE ACCESS"
                  : "NEW ACCOUNT"}
              </span>

              <h1>
                {authMode === "login"
                  ? "Command access"
                  : "Create responder account"}
              </h1>

              <p>
                {authMode === "login"
                  ? "Authenticate to access the emergency response platform."
                  : "Create an account to access emergency coordination services."}
              </p>

            </div>

            {authMode === "login" ? (
              <form
                onSubmit={handleLogin}
              >

                <input
                  type="email"
                  placeholder="Email address"
                  value={loginData.email}
                  onChange={(e) =>
                    setLoginData({
                      ...loginData,
                      email: e.target.value,
                    })
                  }
                  required
                />

                <input
                  type="password"
                  placeholder="Password"
                  value={loginData.password}
                  onChange={(e) =>
                    setLoginData({
                      ...loginData,
                      password: e.target.value,
                    })
                  }
                  required
                />

                <button
                  type="submit"
                  className="primary-action"
                >
                  AUTHENTICATE
                </button>

              </form>
            ) : (
              <form
                onSubmit={handleRegister}
              >

                <input
                  type="text"
                  placeholder="Full name"
                  value={registerData.name}
                  onChange={(e) =>
                    setRegisterData({
                      ...registerData,
                      name: e.target.value,
                    })
                  }
                  required
                />

                <input
                  type="email"
                  placeholder="Email address"
                  value={registerData.email}
                  onChange={(e) =>
                    setRegisterData({
                      ...registerData,
                      email: e.target.value,
                    })
                  }
                  required
                />

                <input
                  type="password"
                  placeholder="Password"
                  value={
                    registerData.password
                  }
                  onChange={(e) =>
                    setRegisterData({
                      ...registerData,
                      password:
                        e.target.value,
                    })
                  }
                  required
                />

                <button
                  type="submit"
                  className="primary-action"
                >
                  CREATE ACCOUNT
                </button>

              </form>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {status && (
              <div className="success-message">
                {status}
              </div>
            )}

            <div className="auth-switch">

              {authMode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}

              <button
                type="button"
                className="text-button"
                onClick={() => {
                  setError("");
                  setStatus("");

                  setAuthMode(
                    authMode === "login"
                      ? "register"
                      : "login"
                  );
                }}
              >
                {authMode === "login"
                  ? "Register"
                  : "Login"}
              </button>

            </div>

          </div>

          <div className="auth-footer">
            JWT authentication · Role-based
            access control · Secure session
          </div>

        </div>
      </div>
    );
  }

  /* =========================
     DASHBOARD DATA
  ========================= */

  const incidentId =
    incident?.id ||
    incident?.incident_id ||
    "—";

  const incidentPriority =
    incident?.priority ||
    incident?.priority_level ||
    "—";

  const incidentStatus =
    incident?.status ||
    status ||
    "WAITING FOR RESPONSE";

  const responderId =
    incident?.responder_id ||
    incident?.responder?.id ||
    "—";

  const assignmentId =
    incident?.assignment_id ||
    incident?.assignment?.id ||
    "—";

  const riskScore =
    incident?.risk_score;

  const priorityReason =
    incident?.priority_reason ||
    "Priority calculated by the risk assessment engine.";

  /* =========================
     DASHBOARD
  ========================= */

  return (
    <div className="command-app">

      {/* HEADER */}

      <header className="command-header">

        <div className="header-brand">

          <div className="brand-mark">
            🚨
          </div>

          <div>
            <div className="brand-name">
              RESPONSECORE
            </div>

            <div className="brand-subtitle">
              Emergency Response Command
              Center
            </div>
          </div>

        </div>

        <div className="header-actions">

          <div className="system-status">

            <span
              className={`status-dot ${
                wsStatus === "LIVE"
                  ? "live"
                  : "offline"
              }`}
            />

            <span>
              {wsStatus === "LIVE"
                ? "SYSTEM LIVE"
                : wsStatus ===
                  "RECONNECTING"
                  ? "RECONNECTING"
                  : "OFFLINE"}
            </span>

          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </header>

      {/* METRICS */}

      <section className="metrics-grid">

        <div className="metric-card">

          <span className="metric-label">
            ACTIVE INCIDENT
          </span>

          <strong className="metric-value">
            {incident
              ? `#${incidentId}`
              : "—"}
          </strong>

          <span className="metric-meta">
            {incident
              ? "Current user session"
              : "No active incident"}
          </span>

        </div>

        <div className="metric-card">

          <span className="metric-label">
            PRIORITY
          </span>

          <strong className="metric-value">
            {incident
              ? String(
                  incidentPriority
                ).toUpperCase()
              : "—"}
          </strong>

          <span className="metric-meta">
            {incident
              ? riskScore !== undefined
                ? `Risk score: ${riskScore}`
                : "Automated priority engine"
              : "Awaiting incident"}
          </span>

        </div>

        <div className="metric-card">

          <span className="metric-label">
            RESPONDER
          </span>

          <strong className="metric-value">
            {responderId !== "—"
              ? `#${responderId}`
              : "—"}
          </strong>

          <span className="metric-meta">
            {responderId !== "—"
              ? "Assigned response unit"
              : "Not assigned"}
          </span>

        </div>

        <div className="metric-card">

          <span className="metric-label">
            LIVE CONNECTION
          </span>

          <strong className="metric-value">
            {wsStatus === "LIVE"
              ? "LIVE"
              : wsStatus}
          </strong>

          <span className="metric-meta">
            WebSocket event channel
          </span>

        </div>

      </section>

      {/* MAIN DASHBOARD */}

      <main className="dashboard-grid">

        {/* INCIDENT INTAKE */}

        <section className="panel report-panel">

          <div className="panel-header">

            <div>

              <span className="eyebrow">
                INCIDENT INTAKE
              </span>

              <h2>
                Report Emergency
              </h2>

              <p>
                Create an emergency incident
                and initiate responder
                coordination.
              </p>

            </div>

            <span className="panel-index">
              01
            </span>

          </div>

          {/* EMERGENCY TYPES */}

          <div className="emergency-options">

            <button
              className={`emergency-button ${
                emergencyType ===
                "Medical Emergency"
                  ? "selected"
                  : ""
              }`}
              onClick={() =>
                setEmergencyType(
                  "Medical Emergency"
                )
              }
            >
              <span>🚑</span>
              <small>Medical</small>
            </button>

            <button
              className={`emergency-button ${
                emergencyType === "Fire"
                  ? "selected"
                  : ""
              }`}
              onClick={() =>
                setEmergencyType("Fire")
              }
            >
              <span>🔥</span>
              <small>Fire</small>
            </button>

            <button
              className={`emergency-button ${
                emergencyType === "Accident"
                  ? "selected"
                  : ""
              }`}
              onClick={() =>
                setEmergencyType(
                  "Accident"
                )
              }
            >
              <span>🚗</span>
              <small>Accident</small>
            </button>

            <button
              className={`emergency-button ${
                emergencyType === "Disaster"
                  ? "selected"
                  : ""
              }`}
              onClick={() =>
                setEmergencyType(
                  "Disaster"
                )
              }
            >
              <span>🌊</span>
              <small>Disaster</small>
            </button>

          </div>

          {/* RISK INPUTS */}

          <div className="risk-inputs">

            <div className="risk-field">

              <label htmlFor="severity">
                INCIDENT SEVERITY
              </label>

              <select
                id="severity"
                value={severity}
                onChange={(e) =>
                  setSeverity(
                    Number(e.target.value)
                  )
                }
              >
                <option value={1}>
                  1 — Minor
                </option>

                <option value={2}>
                  2 — Moderate
                </option>

                <option value={3}>
                  3 — Serious
                </option>

                <option value={4}>
                  4 — Severe
                </option>

                <option value={5}>
                  5 — Extreme
                </option>
              </select>

            </div>

            <div className="risk-field">

              <label htmlFor="peopleAffected">
                PEOPLE AFFECTED
              </label>

              <input
                id="peopleAffected"
                type="number"
                min="0"
                max="100000"
                value={peopleAffected}
                onChange={(e) =>
                  setPeopleAffected(
                    Math.max(
                      0,
                      Number(
                        e.target.value
                      )
                    )
                  )
                }
              />

            </div>

            <div className="risk-field">

              <label htmlFor="peopleTrapped">
                PEOPLE TRAPPED
              </label>

              <input
                id="peopleTrapped"
                type="number"
                min="0"
                max="100000"
                value={peopleTrapped}
                onChange={(e) =>
                  setPeopleTrapped(
                    Math.max(
                      0,
                      Number(
                        e.target.value
                      )
                    )
                  )
                }
              />

            </div>

            <label className="risk-toggle">

              <input
                type="checkbox"
                checked={escalating}
                onChange={(e) =>
                  setEscalating(
                    e.target.checked
                  )
                }
              />

              <span>
                Situation is escalating
              </span>

            </label>

          </div>

          {/* LOCATION */}

          <div className="location">

            <span>📍</span>

            <div>

              <strong>
                GPS LOCATION
              </strong>

              {location ? (
                <>
                  <p>
                    Location detected
                  </p>

                  <small>
                    {location.latitude.toFixed(
                      6
                    )}{" "}
                    ,{" "}
                    {location.longitude.toFixed(
                      6
                    )}
                  </small>
                </>
              ) : (
                <p>
                  {locationStatus}
                </p>
              )}

            </div>

            <span className="row-indicator">
              {location
                ? "READY"
                : "WAIT"}
            </span>

          </div>

          {/* WEBSOCKET */}

          <div className="connection-row">

            <div className="connection-icon">
              ⚡
            </div>

            <div className="connection-content">

              <strong>
                REAL-TIME EVENT CHANNEL
              </strong>

              <span>
                WebSocket
              </span>

            </div>

            <span
              className={`connection-state ${
                wsStatus === "LIVE"
                  ? "live"
                  : "offline"
              }`}
            >
              {wsStatus}
            </span>

          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            className="send-alert"
            onClick={handleSendAlert}
            disabled={
              !location ||
              status ===
                "CREATING INCIDENT"
            }
          >
            {status ===
            "CREATING INCIDENT"
              ? "CREATING INCIDENT..."
              : "🚨 SEND EMERGENCY ALERT"}
          </button>

        </section>

        {/* ACTIVE INCIDENT */}

        <section className="panel incident-panel">

          <div className="panel-header">

            <div>

              <span className="eyebrow">
                ACTIVE INCIDENT
              </span>

              <h2>
                Live Operations
              </h2>

              <p>
                Real-time status of your
                emergency.
              </p>

            </div>

            <span className="panel-index">
              02
            </span>

          </div>

          {!incident ? (
            <div className="empty-state">

              <div className="empty-icon">
                ◌
              </div>

              <strong>
                No active incident
              </strong>

              <span>
                Submit an emergency alert
                to start response
                coordination.
              </span>

            </div>
          ) : (
            <>

              <div className="incident-hero">

                <div>

                  <span className="incident-id">
                    INCIDENT #{incidentId}
                  </span>

                  <h3>
                    {incident.incident_type ||
                      emergencyType}
                  </h3>

                </div>

                <span className="live-badge">
                  LIVE
                </span>

              </div>

              {/* PRIORITY */}

              <div className="priority-badge">
                {String(
                  incidentPriority
                ).toUpperCase()}
              </div>

              {/* RISK ASSESSMENT */}

              <div className="risk-assessment">

                <div className="risk-score">

                  <span>
                    RISK SCORE
                  </span>

                  <strong>
                    {riskScore !== undefined
                      ? riskScore
                      : "—"}
                  </strong>

                </div>

                <div className="risk-reason">

                  <span>
                    ASSESSMENT
                  </span>

                  <p>
                    {riskScore !== undefined
                      ? priorityReason
                      : "Waiting for risk assessment data from the backend."}
                  </p>

                </div>

              </div>

              {/* INCIDENT FACTORS */}

              <div className="incident-details">

                <div className="detail-item">

                  <span>
                    SEVERITY
                  </span>

                  <strong>
                    {incident.severity ??
                      "—"}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    AFFECTED
                  </span>

                  <strong>
                    {incident.people_affected ??
                      "—"}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    TRAPPED
                  </span>

                  <strong>
                    {incident.people_trapped ??
                      "—"}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    ESCALATING
                  </span>

                  <strong>
                    {incident.escalating
                      ? "YES"
                      : "NO"}
                  </strong>

                </div>

              </div>

              {/* STATUS */}

              <div className="incident-status">

                <span className="status-label">
                  CURRENT STATUS
                </span>

                <strong className="status-value">
                  {String(
                    incidentStatus
                  )
                    .replaceAll(
                      "_",
                      " "
                    )
                    .toUpperCase()}
                </strong>

              </div>

              {/* DETAILS */}

              <div className="incident-details">

                <div className="detail-item">

                  <span>
                    PRIORITY
                  </span>

                  <strong>
                    {String(
                      incidentPriority
                    ).toUpperCase()}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    RESPONDER
                  </span>

                  <strong>
                    {responderId !==
                    "—"
                      ? `#${responderId}`
                      : "PENDING"}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    ASSIGNMENT
                  </span>

                  <strong>
                    {assignmentId !==
                    "—"
                      ? `#${assignmentId}`
                      : "PENDING"}
                  </strong>

                </div>

                <div className="detail-item">

                  <span>
                    LOCATION
                  </span>

                  <strong>
                    {location
                      ? "GPS VERIFIED"
                      : "UNAVAILABLE"}
                  </strong>

                </div>

              </div>

              {/* PIPELINE */}

              <div className="pipeline">

                <div className="pipeline-title">
                  RESPONSE PIPELINE
                </div>

                <div className="pipeline-track">

                  <div className="pipeline-step completed">

                    <span>✓</span>

                    <small>
                      CREATED
                    </small>

                  </div>

                  <div className="pipeline-line" />

                  <div
                    className={`pipeline-step ${
                      riskScore !==
                      undefined
                        ? "completed"
                        : ""
                    }`}
                  >

                    <span>
                      {riskScore !==
                      undefined
                        ? "✓"
                        : "2"}
                    </span>

                    <small>
                      PRIORITIZED
                    </small>

                  </div>

                  <div className="pipeline-line" />

                  <div
                    className={`pipeline-step ${
                      responderId !==
                      "—"
                        ? "completed"
                        : ""
                    }`}
                  >

                    <span>
                      {responderId !==
                      "—"
                        ? "✓"
                        : "3"}
                    </span>

                    <small>
                      RESPONDER
                    </small>

                  </div>

                  <div className="pipeline-line" />

                  <div
                    className={`pipeline-step ${
                      assignmentId !==
                      "—"
                        ? "completed"
                        : ""
                    }`}
                  >

                    <span>
                      {assignmentId !==
                      "—"
                        ? "✓"
                        : "4"}
                    </span>

                    <small>
                      ASSIGNED
                    </small>

                  </div>

                </div>

              </div>

            </>
          )}

        </section>

        {/* REAL-TIME EVENT FEED */}

        <section className="panel activity-panel">

          <div className="panel-header">

            <div>

              <span className="eyebrow">
                REAL-TIME EVENTS
              </span>

              <h2>
                Response Activity
              </h2>

              <p>
                Live events received through
                the WebSocket channel.
              </p>

            </div>

            <div className="activity-live">

              <span
                className={`status-dot ${
                  wsStatus === "LIVE"
                    ? "live"
                    : "offline"
                }`}
              />

              {wsStatus === "LIVE"
                ? "LIVE"
                : "OFFLINE"}

            </div>

          </div>

          {events.length === 0 ? (
            <div className="activity-empty">

              <span>◎</span>

              <div>

                <strong>
                  Waiting for system events
                </strong>

                <p>
                  Incident and assignment
                  events will appear here
                  in real time.
                </p>

              </div>

            </div>
          ) : (
            <div className="event-feed">

              {events.map((event) => {

                const isSystem =
                  event.type ===
                  "system";

                return (
                  <div
                    className={`event-item ${
                      isSystem
                        ? "system-event"
                        : ""
                    }`}
                    key={event.id}
                  >

                    <div className="event-icon">
                      {EVENT_ICONS[
                        event.type
                      ] || "•"}
                    </div>

                    <div className="event-content">

                      <div className="event-top">

                        <strong>
                          {isSystem
                            ? "SYSTEM"
                            : EVENT_LABELS[
                                event.type
                              ] ||
                              String(
                                event.type
                              ).toUpperCase()}
                        </strong>

                        <time>
                          {event.time}
                        </time>

                      </div>

                      <p>
                        {isSystem
                          ? event.data
                              ?.message ||
                            "System event"
                          : getEventDetails(
                              event
                            )}
                      </p>

                    </div>

                  </div>
                );

              })}

            </div>
          )}

        </section>

        {/* LIVE DATA */}

        <section className="panel telemetry-panel">

          <div className="panel-header">

            <div>

              <span className="eyebrow">
                LIVE SESSION DATA
              </span>

              <h2>
                Connection State
              </h2>

              <p>
                Actual frontend runtime
                state.
              </p>

            </div>

            <span className="panel-index">
              04
            </span>

          </div>

          <div className="telemetry-grid">

            <div className="telemetry-item">

              <span>
                WEBSOCKET
              </span>

              <strong
                className={
                  wsStatus === "LIVE"
                    ? "healthy"
                    : "unhealthy"
                }
              >
                ● {wsStatus}
              </strong>

            </div>

            <div className="telemetry-item">

              <span>
                GPS
              </span>

              <strong
                className={
                  location
                    ? "healthy"
                    : "unhealthy"
                }
              >
                ●{" "}
                {location
                  ? "READY"
                  : "UNAVAILABLE"}
              </strong>

            </div>

            <div className="telemetry-item">

              <span>
                INCIDENT
              </span>

              <strong>
                {incident
                  ? `#${incidentId}`
                  : "NONE"}
              </strong>

            </div>

            <div className="telemetry-item">

              <span>
                EVENTS RECEIVED
              </span>

              <strong>
                {events.length}
              </strong>

            </div>

          </div>

        </section>

      </main>

      {/* FOOTER */}

      <footer className="command-footer">

        <span>
          RESPONSECORE
        </span>

        <span>
          Real-Time Emergency Coordination
          Platform
        </span>

        <span>
          Session secured
        </span>

      </footer>

    </div>
  );
}

export default App;