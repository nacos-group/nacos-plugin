# Nacos数据库适配插件

## 一、注意事项

### 1.1、修改数据库配置文件

在application.properties文件中声明dameng的配置信息：

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

### 1.3、表结构初始化

在nacos数据库中执行schema/nacos-dm.sql文件，如果不是NACOS模式，需要修改schema/nacos-dm.sql文件中的模式名称
如果表结构没用及时适配，可以使用dameng自带的数据迁移工具进行转换（dameng安装目录/tool/dts.exe 版本8.4.2.98 低版本不识别mysql自增方言）， 或者手动修改表结构