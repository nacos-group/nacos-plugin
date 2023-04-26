# Nacos数据库适配插件

## 一、注意事项

### 1.1、修改数据库配置文件

在application.properties文件中声明postgresql的配置信息：

```java
spring.datasource.platform=dm
        db.url.0=jdbc:dm://127.0.0.1:5236/DMSERVER?schema=NACOS&compatibleMode=mysql&ignoreCase=true&ENCODING=utf-8
        db.user.0=SYSDBA
        db.password.0=SYSDBA
        db.pool.config.driverClassName=dm.jdbc.driver.DmDriver
```

### 1.2、修改dameng数据库配置文件

建议dameng自带的驱动,达梦安装目录下drivers/jdbc下的驱动，否则可能会出现驱动版本不兼容的问题 （读取超长CLOB，TEXT） 替换项目中的lib/DmJdbcDriver18.jar

```xml

<dependency>
    <groupId>com.dameng</groupId>
    <artifactId>DmJdbcDriver18</artifactId>
    <version>${jdbc.dm.version}</version>
    <scope>system</scope>
    <systemPath>${basedir}/lib/DmJdbcDriver18.jar</systemPath>
</dependency>
```