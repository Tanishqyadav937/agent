import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import fs from 'fs';

const loader = new GLTFLoader();
const data = fs.readFileSync('./bunny_character_lipsync.glb');

loader.parse(data, '', (gltf) => {
    console.log('=== GLB STRUCTURE ===');
    console.log('Scene name:', gltf.scene.name);
    console.log('Scene position:', {x: gltf.scene.position.x, y: gltf.scene.position.y, z: gltf.scene.position.z});
    console.log('Scene rotation (rad):', {x: gltf.scene.rotation.x.toFixed(4), y: gltf.scene.rotation.y.toFixed(4), z: gltf.scene.rotation.z.toFixed(4)});
    console.log('Scene rotation (deg):', {x: (gltf.scene.rotation.x * 180/Math.PI).toFixed(2), y: (gltf.scene.rotation.y * 180/Math.PI).toFixed(2), z: (gltf.scene.rotation.z * 180/Math.PI).toFixed(2)});
    console.log('Scene scale:', {x: gltf.scene.scale.x, y: gltf.scene.scale.y, z: gltf.scene.scale.z});
    console.log('Scene children count:', gltf.scene.children.length);
    
    gltf.scene.traverse((obj, idx) => {
        if (obj !== gltf.scene && obj.name && obj.name.match(/[Aa]rmature|root/i)) {
            console.log(`\nFound: ${obj.name} (type: ${obj.type})`);
            console.log('  Position:', {x: obj.position.x, y: obj.position.y, z: obj.position.z});
            console.log('  Rotation (deg):', {x: (obj.rotation.x * 180/Math.PI).toFixed(2), y: (obj.rotation.y * 180/Math.PI).toFixed(2), z: (obj.rotation.z * 180/Math.PI).toFixed(2)});
            console.log('  Scale:', {x: obj.scale.x, y: obj.scale.y, z: obj.scale.z});
            console.log('  Children:', obj.children.length);
        }
    });
}, undefined, (err) => {
    console.error('Error:', err);
    process.exit(1);
});
