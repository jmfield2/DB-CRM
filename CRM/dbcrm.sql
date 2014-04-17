-- MySQL dump 10.11
--
-- Host: localhost    Database: dbcrm
-- ------------------------------------------------------
-- Server version	5.5.35-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Access`
--

DROP TABLE IF EXISTS `Access`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Access` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `created_by` int(11) NOT NULL,
  `access_type` varchar(255) NOT NULL,
  `access_rule` varchar(255) NOT NULL,
  `access_data` varchar(255) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `Access_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Appointments`
--

DROP TABLE IF EXISTS `Appointments`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Appointments` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `service_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `scheduled` datetime NOT NULL,
  `actual` datetime NOT NULL,
  `extra` varchar(255) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `service_id` (`service_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `Appointments_ibfk_4` FOREIGN KEY (`user_id`) REFERENCES `Users` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `Appointments_ibfk_3` FOREIGN KEY (`service_id`) REFERENCES `Services` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Customers`
--

DROP TABLE IF EXISTS `Customers`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Customers` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(255) NOT NULL,
  `customer_type` varchar(255) NOT NULL,
  `primary_contact_id` int(11) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `date_created` datetime DEFAULT NULL,
  `date_modified` datetime DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `primary_contact_id` (`primary_contact_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `Customers_ibfk_8` FOREIGN KEY (`primary_contact_id`) REFERENCES `Customers_Contact` (`ID`) ON DELETE SET NULL ON UPDATE NO ACTION,
  CONSTRAINT `Customers_ibfk_7` FOREIGN KEY (`owner_id`) REFERENCES `Users` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Customers_Contact`
--

DROP TABLE IF EXISTS `Customers_Contact`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Customers_Contact` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `contact_type` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `data` varchar(255) NOT NULL,
  `created_by` int(11) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `name` (`name`,`data`),
  KEY `customer_id` (`customer_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `Customers_Contact_ibfk_4` FOREIGN KEY (`created_by`) REFERENCES `Users` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `Customers_Contact_ibfk_3` FOREIGN KEY (`customer_id`) REFERENCES `Customers` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Quotes`
--

DROP TABLE IF EXISTS `Quotes`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Quotes` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `service_id` int(11) NOT NULL,
  `quote_type` varchar(255) NOT NULL,
  `amount` float NOT NULL,
  `paid` float NOT NULL,
  `owner_id` int(11) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `service_id` (`service_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `Quotes_ibfk_4` FOREIGN KEY (`owner_id`) REFERENCES `Users` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `Quotes_ibfk_3` FOREIGN KEY (`service_id`) REFERENCES `Services` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Services`
--

DROP TABLE IF EXISTS `Services`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Services` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `service_type` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `owner_id` int(11) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `customer_id` (`customer_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `Services_ibfk_4` FOREIGN KEY (`owner_id`) REFERENCES `Users` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `Services_ibfk_3` FOREIGN KEY (`customer_id`) REFERENCES `Customers` (`ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Users`
--

DROP TABLE IF EXISTS `Users`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Users` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Username` varchar(255) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `status` int(11) NOT NULL,
  `Company` varchar(255) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-04-17 17:10:36
