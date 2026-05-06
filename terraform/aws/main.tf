terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "gravit_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "gravit-vpc-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.gravit_vpc.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "gravit-public-subnet-${count.index}"
    Environment = var.environment
  }
}

resource "aws_internet_gateway" "gravit_igw" {
  vpc_id = aws_vpc.gravit_vpc.id

  tags = {
    Name        = "gravit-igw-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.gravit_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gravit_igw.id
  }

  tags = {
    Name        = "gravit-public-rt-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "gravit_api" {
  name        = "gravit-api-sg-${var.environment}"
  description = "Security group for Gravit API"
  vpc_id      = aws_vpc.gravit_vpc.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "API Gateway"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "gravit-api-sg-${var.environment}"
    Environment = var.environment
  }
}

output "vpc_id" {
  value = aws_vpc.gravit_vpc.id
}
