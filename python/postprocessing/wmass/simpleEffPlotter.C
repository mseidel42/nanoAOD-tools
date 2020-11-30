#include "TFile.h"
#include "TH1F.h"
#include "TTree.h"
#include "TMath.h"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <iostream>

using RDF = ROOT::RDataFrame;
using RVecF = ROOT::VecOps::RVec<float>;
using RVecI = ROOT::VecOps::RVec<int>;
using namespace std;

int plot(){

  ROOT::EnableImplicitMT();

  RDF d("Events", "SMP-RunIISummer16NanoAODv8-wmassNano_default_numEvent10000_Skim.root" );  
  cout << "Total events:" << *(d.Count()) << endl; 

  auto d_TrkIsoId = d.Filter("nPairTrk>0");
  cout << ">0 pairs:" << *(d_TrkIsoId.Count()) << endl; 

  auto tnp_pair_mass =  []( int nPair, RVecI Idx_tag, RVecI Idx_probe, RVecF Muon_pt, RVecF Muon_eta, RVecF Muon_phi )->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      int i_tag   = Idx_tag.at(i);
      int i_probe = Idx_probe.at(i) ;
      float mu1_pt  = Muon_pt.at(i_tag);
      float mu1_eta = Muon_eta.at(i_tag);
      float mu1_phi = Muon_phi.at(i_tag);
      float mu2_pt  = Muon_pt.at(i_probe);
      float mu2_eta = Muon_eta.at(i_probe);
      float mu2_phi = Muon_phi.at(i_probe);
      float e  = mu1_pt*TMath::CosH(mu1_eta) + mu2_pt*TMath::CosH(mu2_eta);
      float px = mu1_pt*TMath::Cos(mu1_phi)  + mu2_pt*TMath::Cos(mu2_phi);
      float py = mu1_pt*TMath::Sin(mu1_phi)  + mu2_pt*TMath::Sin(mu2_phi);
      float pz = mu1_pt*TMath::SinH(mu1_eta) + mu2_pt*TMath::SinH(mu2_eta);
      float mass = TMath::Sqrt(e*e - px*px - py*py - pz*pz);
      v.emplace_back(mass);
    }
    return v;
  };

  auto tnp_probe_pt =  []( int nPair, RVecI Idx_probe, RVecF Muon_pt)->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      int i_probe = Idx_probe.at(i) ;
      float mu_pt  = Muon_pt.at(i_probe);
      v.emplace_back(mu_pt);
    }
    return v;
  };

  auto tnp_pair_mass_pass = []( int nPair, RVecI Is_pass, RVecF Pair_mass )->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      if(Is_pass.at(i)<1) continue;
      v.emplace_back(Pair_mass.at(i));
    }
    return v;
  };
  auto tnp_pair_mass_fail = []( int nPair, RVecI Is_pass, RVecF Pair_mass )->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      if(Is_pass.at(i)>0) continue;
      v.emplace_back(Pair_mass.at(i));
    }
    return v;
  };
  auto tnp_probe_pt_pass = []( int nPair, RVecI Is_pass, RVecF Probe_pt )->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      if(Is_pass.at(i)<1) continue;
      v.emplace_back(Probe_pt.at(i));
    }
    return v;
  };
  auto tnp_probe_pt_fail = []( int nPair, RVecI Is_pass, RVecF Probe_pt )->RVecF {
    RVecF v;
    for(int i = 0; i < nPair; i++){
      if(Is_pass.at(i)>0) continue;
      v.emplace_back(Probe_pt.at(i));
    }
    return v;
  };

  auto d_post = d_TrkIsoId    
    .Define("PairTrk_mass", tnp_pair_mass,{"nPairTrk", "Idx_tagTrk", "Idx_probeTrk", "Muon_pt", "Muon_eta", "Muon_phi"})
    .Define("ProbeTrk_pt",  tnp_probe_pt, {"nPairTrk", "Idx_probeTrk", "Muon_pt"})
    .Define("ProbeTrk_eta", tnp_probe_pt, {"nPairTrk", "Idx_probeTrk", "Muon_eta"})
    .Define("PairTrkPass_mass", tnp_pair_mass_pass, {"nPairTrk", "Is_passTrkIdIso", "PairTrk_mass"})
    .Define("PairTrkFail_mass", tnp_pair_mass_fail, {"nPairTrk", "Is_passTrkIdIso", "PairTrk_mass"})
    .Define("ProbeTrkPass_pt",  tnp_probe_pt_pass,  {"nPairTrk", "Is_passTrkIdIso", "ProbeTrk_pt"})
    .Define("ProbeTrkFail_pt",  tnp_probe_pt_fail,  {"nPairTrk", "Is_passTrkIdIso", "ProbeTrk_pt"})
    .Define("ProbeTrkPass_eta",  tnp_probe_pt_pass, {"nPairTrk", "Is_passTrkIdIso", "ProbeTrk_eta"})
    .Define("ProbeTrkFail_eta",  tnp_probe_pt_fail, {"nPairTrk", "Is_passTrkIdIso", "ProbeTrk_eta"})
    ;

  auto hPass = d_post.Histo3D<RVecF,RVecF,RVecF>( {"TrkPass", "", 60, 60, 120, 30, 30, 60, 48, -2.4, 2.4}, "PairTrkPass_mass", "ProbeTrkPass_pt", "ProbeTrkPass_eta" ); 
  auto hFail = d_post.Histo3D<RVecF,RVecF,RVecF>( {"TrkFail", "", 60, 60, 120, 30, 30, 80, 48, -2.4, 2.4}, "PairTrkFail_mass", "ProbeTrkFail_pt", "ProbeTrkFail_eta" ); 

  TFile* out = TFile::Open("out.root", "RECREATE");
  out->cd();
  hPass->Write("", TObject::kOverwrite);
  out->Close();

  return 0;
}
