/*
 * Copyright 1999-2021 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.alibaba.nacos.plugin.encryption;

/**
 * The server is configured with encryption and decryption implementation. Re encrypt the secret key, and the secret key
 * of the encrypted secret key is only saved at the server.
 *
 * @author hujun
 */
public class ServerAesEncryptionPluginService extends AesEncryptionPluginService {
    
    private final String parentSecret;
    
    {
        parentSecret = System.getProperty("nacos.encrypt", "nacos");
    }
    
    /**
     * The server decrypts the configuration, such as viewing the configuration on the console.
     *
     * @param secretKey Encrypted secret key
     * @param content   Configuration content
     * @return Decrypt content
     */
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
    
    /**
     * Define the encryption algorithm for configuring the secret key. Here, simply use AES
     *
     * @param secretKey Secret key plaintext
     * @return Secret key ciphertext
     */
    @Override
    public String encryptSecretKey(String secretKey) {
        return super.encrypt(parentSecret, secretKey);
    }
    
    /**
     * Define the decryption algorithm for the secret key decryption, which should correspond to the encryption
     * algorithm of the secret key.
     *
     * @param secretKey Secret key ciphertext
     * @return Secret key plaintext
     */
    @Override
    public String decryptSecretKey(String secretKey) {
        return super.decrypt(parentSecret, secretKey);
    }
}
