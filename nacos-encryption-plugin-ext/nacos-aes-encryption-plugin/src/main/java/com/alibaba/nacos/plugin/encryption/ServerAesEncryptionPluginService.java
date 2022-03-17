package com.alibaba.nacos.plugin.encryption;


/**
 * server encrypt impl.
 * @author hujun
 */
public class ServerAesEncryptionPluginService extends AesEncryptionPluginService {
    
    private final String parentSecret;
    
    {
        parentSecret = System.getProperty("nacos.encrypt");
    }
    
    @Override
    public String decrypt(String secretKey, String content) {
        //获取本地秘钥
        String secret = super.decrypt(parentSecret, secretKey);
        return super.decrypt(secret, content);
    }
    
    @Override
    public String algorithmName() {
        return "doubleAes";
    }
    
    @Override
    public String encryptSecretKey(String secretKey) {
        return super.encrypt(parentSecret, secretKey);
    }
    
    @Override
    public String decryptSecretKey(String secretKey) {
        return super.decrypt(parentSecret, secretKey);
    }
}
