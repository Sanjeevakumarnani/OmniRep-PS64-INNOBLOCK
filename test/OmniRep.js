const { expect } = require("chai");
const { ethers } = require("hardhat");

const DOMAIN = { name:"OmniRep Passport", version:"1", salt:ethers.keccak256(ethers.toUtf8Bytes("OmniRep.Portable.Attestation.v1")) };
const TYPES = { Attestation:[
 {name:"id",type:"uint256"},{name:"score",type:"uint16"},{name:"sybilRisk",type:"uint8"},{name:"algoVersion",type:"uint16"},{name:"linkedCount",type:"uint8"},{name:"inputHash",type:"bytes32"},{name:"linksHash",type:"bytes32"},{name:"version",type:"uint32"},{name:"deadline",type:"uint64"}
]};

describe("OmniRepRegistry",function(){
 it("creates passports and accepts only an attestor-signed publication",async function(){
  const [owner,attestor,other]=await ethers.getSigners();
  const reg=await ethers.deployContract("OmniRepRegistry",[owner.address,attestor.address]); await reg.waitForDeployment();
  const tx=await reg.createPassport(); const rc=await tx.wait(); const id=rc.logs.find(x=>x.fragment?.name==="PassportCreated").args[0];
  const input=ethers.sha256(ethers.toUtf8Bytes("inputs")); const links=ethers.sha256(ethers.toUtf8Bytes("links"));
  const a={id,score:520,sybilRisk:12,algoVersion:10001,linkedCount:2,inputHash:input,linksHash:links,version:1,deadline:Math.floor(Date.now()/1000)+900};
  const sig=await attestor.signTypedData(DOMAIN,TYPES,a);
  await expect(reg.publish(a,sig)).to.emit(reg,"ScorePublished");
  expect(await reg.scoreOf(id)).to.equal(520); expect(await reg.tierOf(id)).to.equal(2); expect(await reg.verifyInputs(id,input)).to.equal(true); expect(await reg.verifyInputBytes(id,ethers.toUtf8Bytes("inputs"))).to.equal(true);
  await expect(reg.connect(other).publish({...a,version:2,score:800},sig)).to.be.revertedWith("not passport owner");
 });
 it("rejects replay or bad version",async function(){
  const [owner,attestor]=await ethers.getSigners();const reg=await ethers.deployContract("OmniRepRegistry",[owner.address,attestor.address]);await reg.waitForDeployment();
  const tx=await reg.createPassport();const rc=await tx.wait();const id=rc.logs.find(x=>x.fragment?.name==="PassportCreated").args[0];
  const a={id,score:400,sybilRisk:0,algoVersion:10001,linkedCount:2,inputHash:ethers.id("i"),linksHash:ethers.id("l"),version:1,deadline:Math.floor(Date.now()/1000)+900};
  const sig=await attestor.signTypedData(DOMAIN,TYPES,a);await reg.publish(a,sig);await expect(reg.publish(a,sig)).to.be.revertedWith("bad version");
 });
});

describe("OmniRep Playground",function(){
 it("emits the typed evidence events",async function(){const [a]=await ethers.getSigners();const loan=await ethers.deployContract("OmniRepLoanPool");await loan.waitForDeployment();const gov=await ethers.deployContract("OmniRepGovernor");await gov.waitForDeployment();const con=await ethers.deployContract("OmniRepContributionLog");await con.waitForDeployment();const b=await loan.borrowAndRepay(100);const br=await b.wait();expect(br.logs.some(x=>x.fragment?.name==="Borrowed")).to.equal(true);expect(br.logs.some(x=>x.fragment?.name==="Repaid")).to.equal(true);const d=await loan.borrowAndDefault(100);const dr=await d.wait();expect(dr.logs.some(x=>x.fragment?.name==="Defaulted")).to.equal(true);const p=await gov.createProposal("test");const pr=await p.wait();const pid=pr.logs.find(x=>x.fragment?.name==="ProposalCreated").args[0];await expect(gov.vote(pid,true)).to.emit(gov,"Voted");await expect(con.contribute(ethers.id("project"),100)).to.emit(con,"Contributed");});
});
