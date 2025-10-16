#!/bin/zsh
# Utility script to print SQL Server connection info for universal-parquet-exporter

echo "Enter SQL Server port (default: 1433):"
echo "Enter SQL Server database name:"
echo "Enter SQL Server username:"
echo "Enter SQL Server password (input will be hidden):"
echo

conf_file=".confSQLConnection"
# Load existing values if file exists
if [ -f "$conf_file" ]; then
	echo "Found existing $conf_file in the current directory."
	source "$conf_file"
else
	SQLSERVER_HOST=""
	SQLSERVER_PORT=""
	SQLSERVER_DATABASE=""
	SQLSERVER_USER=""
	SQLSERVER_PASSWORD=""
fi


# Detect shell type
if [ -n "$BASH_VERSION" ]; then
	SHELL_TYPE="bash"
else
	SHELL_TYPE="zsh"
fi

# Helper function for prompting
prompt_input() {
	local prompt="$1"
	local varname="$2"
	if [ "$SHELL_TYPE" = "bash" ]; then
		read -p "$prompt" $varname
	else
		print -n "$prompt"
		read $varname
	fi
}

echo "Enter SQL Server host (default: localhost):"
if [ -n "$SQLSERVER_HOST" ]; then
	echo "Current: $SQLSERVER_HOST"
	prompt_input "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		host="$SQLSERVER_HOST"
	else
		prompt_input "Enter new host: " host
		host=${host:-localhost}
	fi
else
	prompt_input "" host
	host=${host:-localhost}
fi

echo "Enter SQL Server port (default: 1433):"
if [ -n "$SQLSERVER_PORT" ]; then
	echo "Current: $SQLSERVER_PORT"
	prompt_input "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		port="$SQLSERVER_PORT"
	else
		prompt_input "Enter new port: " port
		port=${port:-1433}
	fi
else
	prompt_input "" port
	port=${port:-1433}
fi

echo "Enter SQL Server database name:"
if [ -n "$SQLSERVER_DATABASE" ]; then
	echo "Current: $SQLSERVER_DATABASE"
	prompt_input "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		database="$SQLSERVER_DATABASE"
	else
		prompt_input "Enter new database: " database
	fi
else
	prompt_input "" database
fi

echo "Enter SQL Server username:"
if [ -n "$SQLSERVER_USER" ]; then
	echo "Current: $SQLSERVER_USER"
	prompt_input "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		username="$SQLSERVER_USER"
	else
		prompt_input "Enter new username: " username
	fi
else
	prompt_input "" username
fi

echo "Enter SQL Server password (input will be hidden):"
if [ -n "$SQLSERVER_PASSWORD" ]; then
	echo "Current: (hidden)"
	prompt_input "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		password="$SQLSERVER_PASSWORD"
	else
		if [ "$SHELL_TYPE" = "bash" ]; then
			stty -echo
			read -p "Enter new password: " password
			stty echo
			echo
		else
			print -n "Enter new password: "
			stty -echo
			read password
			stty echo
			echo
		fi
	fi
else
	if [ "$SHELL_TYPE" = "bash" ]; then
		stty -echo
		read -p "" password
		stty echo
		echo
	else
		stty -echo
		read password
		stty echo
		echo
	fi
fi



# Save connection details to .confSQLConnection
cat > "$conf_file" << EOF
SQLSERVER_HOST=$host
SQLSERVER_PORT=$port
SQLSERVER_DATABASE=$database
SQLSERVER_USER=$username
SQLSERVER_PASSWORD=$password
EOF

echo "\n--- SQL Server Connection Information ---"
echo "Connection string for pyodbc:"
echo "DRIVER={ODBC Driver 17 for SQL Server};SERVER=$host,$port;DATABASE=$database;UID=$username;PWD=$password"
echo "\nEnvironment variable exports (optional):"
echo "export SQLSERVER_HOST=$host"
echo "export SQLSERVER_PORT=$port"
echo "export SQLSERVER_DATABASE=$database"
echo "export SQLSERVER_USER=$username"
echo "export SQLSERVER_PASSWORD=********" # Do not print actual password for security
echo "\nConnection details saved to $conf_file. Copy and use these values in your config/sqlserver_config.py or as environment variables."
