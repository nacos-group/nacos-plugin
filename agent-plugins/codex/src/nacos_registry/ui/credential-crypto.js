/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosCredentialCrypto = (() => {
  const b64 = bytes => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const decode = text => Uint8Array.from(atob(text.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
  async function seal(channel, payload) {
    let clear, keyBytes;
    try {
      if (channel?.mode !== 'mcp-jwe-v1' || !/^[A-Za-z0-9_-]{43}$/.test(channel.sessionId || '')
          || !/^[A-Za-z0-9_-]{300,700}$/.test(channel.publicKey || '') || !globalThis.crypto?.subtle) throw new Error();
      const subtle = crypto.subtle, encode = value => new TextEncoder().encode(value);
      const key = await subtle.importKey('spki', decode(channel.publicKey), {name:'RSA-OAEP', hash:'SHA-256'}, false, ['encrypt']);
      if (key.algorithm.modulusLength !== 2048) throw new Error();
      clear = encode(JSON.stringify(payload));
      if (clear.length > 32768) throw new Error();
      keyBytes = crypto.getRandomValues(new Uint8Array(64));
      const iv = crypto.getRandomValues(new Uint8Array(16));
      const protectedHeader = b64(encode(JSON.stringify({alg:'RSA-OAEP-256', enc:'A256CBC-HS512', kid:channel.sessionId})));
      const aad = encode(protectedHeader), length = new Uint8Array(8);
      new DataView(length.buffer).setBigUint64(0, BigInt(aad.length * 8));
      const aes = await subtle.importKey('raw', keyBytes.slice(32), 'AES-CBC', false, ['encrypt']);
      const mac = await subtle.importKey('raw', keyBytes.slice(0,32), {name:'HMAC', hash:'SHA-512'}, false, ['sign']);
      const ciphertext = new Uint8Array(await subtle.encrypt({name:'AES-CBC', iv}, aes, clear));
      const authenticated = new Uint8Array(aad.length + iv.length + ciphertext.length + length.length);
      authenticated.set(aad); authenticated.set(iv, aad.length); authenticated.set(ciphertext, aad.length+iv.length);
      authenticated.set(length, authenticated.length-length.length);
      const tag = new Uint8Array(await subtle.sign('HMAC', mac, authenticated)).slice(0,32);
      const wrapped = await subtle.encrypt({name:'RSA-OAEP'}, key, keyBytes);
      return [protectedHeader,b64(wrapped),b64(iv),b64(ciphertext),b64(tag)].join('.');
    } catch {
      throw Object.assign(new Error('页面加密不可用，请重新打开资源中心。'), {kind:'credential_crypto'});
    } finally { clear?.fill(0); keyBytes?.fill(0); }
  }
  return {seal};
})();
