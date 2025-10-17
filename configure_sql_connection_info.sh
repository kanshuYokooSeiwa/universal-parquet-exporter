#!/usr/bin/env zsh
# Cross-shell (bash/zsh) interactive configurator for SQL Server env vars
# - Reads existing values from .confSQLConnection if present
# - Prompts to confirm/update missing or existing values
# - Writes (and overwrites) .confSQLConnection with export lines
# - When sourced (recommended), exports vars into current shell

set -e

conf_file=".confSQLConnection"

# Detect shell type for prompt behavior
if [ -n "$BASH_VERSION" ]; then
  SHELL_TYPE="bash"
else
  SHELL_TYPE="zsh"
fi

# Helper prompt function compatible with bash and zsh
prompt_input() {
  local prompt="$1"
  local _outvar="$2"
  if [ "$SHELL_TYPE" = "bash" ]; then
    read -p "$prompt" "$_outvar"
  else
    print -n "$prompt"
    read "$_outvar"
  fi
}

# Source existing conf if present to prefill values
if [ -f "$conf_file" ]; then
  echo "Found existing $conf_file. Prefilling current values."
  # shellcheck disable=SC1090
  source "$conf_file"
fi

# Ensure variables exist even if not set by source
: ${SQLSERVER_HOST:=""}
: ${SQLSERVER_PORT:=""}
: ${SQLSERVER_DATABASE:=""}
: ${SQLSERVER_USER:=""}
: ${SQLSERVER_PASSWORD:=""}
: ${SQLSERVER_ENCRYPT:=""}
: ${SQLSERVER_TRUST_CERT:=""}

# Host
echo "Enter SQL Server host (default: localhost):"
if [ -n "$SQLSERVER_HOST" ]; then
  echo "Current: $SQLSERVER_HOST"
  prompt_input "Is this correct? (y/n): " correct
  if [ "$correct" != "y" ]; then
    prompt_input "Enter new host: " SQLSERVER_HOST
  fi
fi
if [ -z "$SQLSERVER_HOST" ]; then
  prompt_input "" SQLSERVER_HOST
  SQLSERVER_HOST=${SQLSERVER_HOST:-localhost}
fi

# Port
echo "Enter SQL Server port (default: 1433):"
if [ -n "$SQLSERVER_PORT" ]; then
  echo "Current: $SQLSERVER_PORT"
  prompt_input "Is this correct? (y/n): " correct
  if [ "$correct" != "y" ]; then
    prompt_input "Enter new port: " SQLSERVER_PORT
  fi
fi
if [ -z "$SQLSERVER_PORT" ]; then
  prompt_input "" SQLSERVER_PORT
  SQLSERVER_PORT=${SQLSERVER_PORT:-1433}
fi

# Database
echo "Enter SQL Server database name:"
if [ -n "$SQLSERVER_DATABASE" ]; then
  echo "Current: $SQLSERVER_DATABASE"
  prompt_input "Is this correct? (y/n): " correct
  if [ "$correct" != "y" ]; then
    prompt_input "Enter new database: " SQLSERVER_DATABASE
  fi
fi
if [ -z "$SQLSERVER_DATABASE" ]; then
  prompt_input "" SQLSERVER_DATABASE
fi

# Username
echo "Enter SQL Server username:"
if [ -n "$SQLSERVER_USER" ]; then
  echo "Current: $SQLSERVER_USER"
  prompt_input "Is this correct? (y/n): " correct
  if [ "$correct" != "y" ]; then
    prompt_input "Enter new username: " SQLSERVER_USER
  fi
fi
if [ -z "$SQLSERVER_USER" ]; then
  prompt_input "" SQLSERVER_USER
fi

# Password (hidden)
echo "Enter SQL Server password (input will be hidden):"
if [ -n "$SQLSERVER_PASSWORD" ]; then
  echo "Current: (hidden)"
  prompt_input "Is this correct? (y/n): " correct
  if [ "$correct" != "y" ]; then
    if [ "$SHELL_TYPE" = "bash" ]; then
      stty -echo; read -p "Enter new password: " SQLSERVER_PASSWORD; stty echo; echo
    else
      print -n "Enter new password: "; stty -echo; read SQLSERVER_PASSWORD; stty echo; echo
    fi
  fi
fi
if [ -z "$SQLSERVER_PASSWORD" ]; then
  if [ "$SHELL_TYPE" = "bash" ]; then
    stty -echo; read -p "" SQLSERVER_PASSWORD; stty echo; echo
  else
    stty -echo; read SQLSERVER_PASSWORD; stty echo; echo
  fi
fi

# Encrypt and TrustServerCertificate (optional with defaults)
if [ -z "$SQLSERVER_ENCRYPT" ]; then SQLSERVER_ENCRYPT="yes"; fi
if [ -z "$SQLSERVER_TRUST_CERT" ]; then SQLSERVER_TRUST_CERT="yes"; fi

# Write export lines to config file
cat > "$conf_file" << EOF
export SQLSERVER_HOST="$SQLSERVER_HOST"
export SQLSERVER_PORT="$SQLSERVER_PORT"
export SQLSERVER_DATABASE="$SQLSERVER_DATABASE"
export SQLSERVER_USER="$SQLSERVER_USER"
export SQLSERVER_PASSWORD="$SQLSERVER_PASSWORD"
export SQLSERVER_ENCRYPT="$SQLSERVER_ENCRYPT"
export SQLSERVER_TRUST_CERT="$SQLSERVER_TRUST_CERT"
EOF

echo "Saved environment configuration to $conf_file"

# If the script is sourced, export into current shell now
# Detect if sourced in bash or zsh
is_sourced=false
# zsh: $ZSH_EVAL_CONTEXT contains :file if sourced
if [ -n "$ZSH_EVAL_CONTEXT" ] && [[ $ZSH_EVAL_CONTEXT == *:file ]]; then
  is_sourced=true
fi
# bash: check if $0 != $BASH_SOURCE
if [ -n "$BASH_VERSION" ] && [ "$0" != "$BASH_SOURCE" ]; then
  is_sourced=true
fi


# Explicitly export each variable if sourced
if $is_sourced; then
  export SQLSERVER_HOST="$SQLSERVER_HOST"
  export SQLSERVER_PORT="$SQLSERVER_PORT"
  export SQLSERVER_DATABASE="$SQLSERVER_DATABASE"
  export SQLSERVER_USER="$SQLSERVER_USER"
  export SQLSERVER_PASSWORD="$SQLSERVER_PASSWORD"
  export SQLSERVER_ENCRYPT="$SQLSERVER_ENCRYPT"
  export SQLSERVER_TRUST_CERT="$SQLSERVER_TRUST_CERT"
  echo "Environment variables exported into current shell."
else
  echo "Tip: To export variables into your current shell, run:"
  echo "  export SQLSERVER_HOST=\"$SQLSERVER_HOST\""
  echo "  export SQLSERVER_PORT=\"$SQLSERVER_PORT\""
  echo "  export SQLSERVER_DATABASE=\"$SQLSERVER_DATABASE\""
  echo "  export SQLSERVER_USER=\"$SQLSERVER_USER\""
  echo "  export SQLSERVER_PASSWORD=\"$SQLSERVER_PASSWORD\""
  echo "  export SQLSERVER_ENCRYPT=\"$SQLSERVER_ENCRYPT\""
  echo "  export SQLSERVER_TRUST_CERT=\"$SQLSERVER_TRUST_CERT\""
fi

# Show connection string (masked password) and summary
echo
echo "--- SQL Server Connection Information ---"
echo "Host: $SQLSERVER_HOST"
echo "Port: $SQLSERVER_PORT"
echo "Database: $SQLSERVER_DATABASE"
echo "User: $SQLSERVER_USER"
echo "Encrypt: $SQLSERVER_ENCRYPT, TrustServerCertificate: $SQLSERVER_TRUST_CERT"
echo "Connection string (pyodbc):"
echo "DRIVER={ODBC Driver 18 for SQL Server};SERVER=$SQLSERVER_HOST,$SQLSERVER_PORT;DATABASE=$SQLSERVER_DATABASE;UID=$SQLSERVER_USER;PWD=********;Encrypt=$SQLSERVER_ENCRYPT;TrustServerCertificate=$SQLSERVER_TRUST_CERT"
