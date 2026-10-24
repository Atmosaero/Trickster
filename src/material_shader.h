#pragma once
namespace trickster {
inline constexpr const char *cpuMaterialVertexShader = R"GLSL(
#version 120
varying vec3 worldPosition;
varying vec3 worldNormal;
varying vec2 uv0;
varying vec2 uv1;
void main(){worldPosition=gl_Vertex.xyz;worldNormal=gl_Normal;uv0=gl_MultiTexCoord0.xy;uv1=gl_MultiTexCoord1.xy;gl_Position=gl_ModelViewProjectionMatrix*gl_Vertex;}
)GLSL";
inline constexpr const char *materialVertexShader = R"GLSL(
#version 120
varying vec3 worldPosition;
varying vec3 worldNormal;
varying vec2 uv0;
varying vec2 uv1;
uniform bool useSkinning;
uniform sampler2D skinPalette;
uniform float paletteRows;
attribute vec4 skinIndices0,skinIndices1,skinWeights0,skinWeights1;
mat4 boneMatrix(float index,float normalRow) {
    float y=(index*2.0+normalRow+0.5)/paletteRows;
    return mat4(texture2D(skinPalette,vec2(0.125,y)),texture2D(skinPalette,vec2(0.375,y)),texture2D(skinPalette,vec2(0.625,y)),texture2D(skinPalette,vec2(0.875,y)));
}
void main() {
    worldPosition=gl_Vertex.xyz;
    worldNormal=gl_Normal;
    if(useSkinning) {
        vec4 p=vec4(0.0),n=vec4(0.0);float total=0.0;
        for(int i=0;i<4;++i) {
            float a=skinWeights0[i],b=skinWeights1[i];
            if(a>0.0){p+=a*(boneMatrix(skinIndices0[i],0.0)*gl_Vertex);n+=a*(boneMatrix(skinIndices0[i],1.0)*vec4(gl_Normal,0.0));total+=a;}
            if(b>0.0){p+=b*(boneMatrix(skinIndices1[i],0.0)*gl_Vertex);n+=b*(boneMatrix(skinIndices1[i],1.0)*vec4(gl_Normal,0.0));total+=b;}
        }
        if(total>0.000001){worldPosition=p.xyz/total;worldNormal=normalize(n.xyz);}
    }
    uv0=gl_MultiTexCoord0.xy;
    uv1=gl_MultiTexCoord1.xy;
    gl_Position=gl_ModelViewProjectionMatrix*vec4(worldPosition,1.0);
}
)GLSL";
inline constexpr const char *materialFragmentShader = R"GLSL(
#version 120
varying vec3 worldPosition;
varying vec3 worldNormal;
varying vec2 uv0;
varying vec2 uv1;
uniform sampler2D baseMap,normalMap,ormMap,aoMap,emissiveMap;
uniform bool hasBase,hasNormal,hasOrm,hasAo,hasEmissive,unlit;
uniform vec4 baseTransform,normalTransform,ormTransform,aoTransform,emissiveTransform;
uniform vec3 baseUV,normalUV,ormUV,aoUV,emissiveUV;
uniform vec4 baseFactor;
uniform vec3 emission,cameraPosition;
uniform float metallic,roughness,normalScale,aoStrength,alphaCutoff;
uniform int alphaMode;
vec2 coords(vec4 transform,vec3 info) {
    vec2 uv=(info.z>0.5?uv1:uv0)*transform.xy;
    return mat2(info.x,info.y,-info.y,info.x)*uv+transform.zw;
}
vec3 srgbToLinear(vec3 v){return pow(max(v,vec3(0.0)),vec3(2.2));}
void main(){
    vec4 base=baseFactor;
    if(hasBase){vec4 tex=texture2D(baseMap,coords(baseTransform,baseUV));base*=vec4(srgbToLinear(tex.rgb),tex.a);}
    if(alphaMode==1 && base.a<alphaCutoff)discard;
    if(unlit){gl_FragColor=vec4(pow(max(base.rgb,vec3(0.0)),vec3(1.0/2.2)),alphaMode==2?base.a:1.0);return;}
    vec3 N=normalize(worldNormal);if(!gl_FrontFacing)N=-N;
    if(hasNormal){
        vec2 uv=coords(normalTransform,normalUV);
        vec3 dp1=dFdx(worldPosition),dp2=dFdy(worldPosition);
        vec2 duv1=dFdx(uv),duv2=dFdy(uv);
        vec3 p2=cross(dp2,N),p1=cross(N,dp1);
        vec3 T=p2*duv1.x+p1*duv2.x,B=p2*duv1.y+p1*duv2.y;
        float inv=inversesqrt(max(max(dot(T,T),dot(B,B)),1e-12));
        vec3 map=texture2D(normalMap,uv).xyz*2.0-1.0;map.xy*=normalScale;
        N=normalize(mat3(T*inv,B*inv,N)*map);
    }
    float metal=metallic,rough=roughness;
    if(hasOrm){vec3 orm=texture2D(ormMap,coords(ormTransform,ormUV)).rgb;rough*=orm.g;metal*=orm.b;}
    rough=clamp(rough,0.045,1.0);metal=clamp(metal,0.0,1.0);
    vec3 V=normalize(cameraPosition-worldPosition),L=normalize(vec3(-0.6,0.9,0.8)),H=normalize(V+L);
    float nv=max(dot(N,V),0.001),nl=max(dot(N,L),0.0),nh=max(dot(N,H),0.0),vh=max(dot(V,H),0.0);
    float a=rough*rough,a2=a*a,den=nh*nh*(a2-1.0)+1.0,D=a2/(3.14159265*den*den);
    float k=(rough+1.0)*(rough+1.0)/8.0,G=nv/(nv*(1.0-k)+k)*nl/(nl*(1.0-k)+k);
    vec3 f0=mix(vec3(0.04),base.rgb,metal),F=f0+(vec3(1.0)-f0)*pow(1.0-vh,5.0);
    vec3 specular=D*G*F/max(4.0*nv*nl,0.001),diffuse=(vec3(1.0)-F)*(1.0-metal)*base.rgb/3.14159265;
    float ao=hasAo?mix(1.0,texture2D(aoMap,coords(aoTransform,aoUV)).r,aoStrength):1.0;
    vec3 emissive=emission;if(hasEmissive)emissive*=srgbToLinear(texture2D(emissiveMap,coords(emissiveTransform,emissiveUV)).rgb);
    vec3 color=(diffuse+specular)*nl*3.0+base.rgb*(0.14+0.12*max(N.y,0.0))*ao+emissive;
    color=color/(color+vec3(1.0));
    gl_FragColor=vec4(pow(max(color,vec3(0.0)),vec3(1.0/2.2)),alphaMode==2?base.a:1.0);
}
)GLSL";
} // namespace trickster
