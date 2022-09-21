FROM python:3.9

LABEL maintainer="Yohans"

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -qq -y \
    git gcc build-essential libpq-dev --fix-missing --no-install-recommends \ 
    && apt-get clean

# latest version of pip
RUN pip install --upgrade pip

# Create directory for dbt config
RUN mkdir -p /root/.dbt

# Copy requirements.txt
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy dbt profile
COPY profiles.yml /root/.dbt/profiles.yml

# Copy source code
COPY ./scalable_dwh_dbt /app

# Export environement variables for dbt

# Start the dbt
CMD ["dbt-rpc", "serve"]