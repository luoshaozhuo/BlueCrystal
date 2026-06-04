"""Whale 共享 ORM 模型."""

from whale.shared.persistence.orm.acquisition import (
    AcquisitionTask,
    AcqSignalSample,
    AcqSignalState,
)
from whale.shared.persistence.orm.asset import (
    AssetAttribute,
    AssetBOM,
    AssetInstance,
    AssetModel,
    AssetRelation,
    AssetType,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from whale.shared.persistence.orm.ingest_diagnostics import (
    IngestRuntimeEventOrm,
    IngestSourceHealthOrm,
)
from whale.shared.persistence.orm.ingest_runtime import (
    IngestAuditEventOrm,
    IngestBundleMetadata,
    IngestFencingToken,
    IngestJobAssignment,
    IngestJobLease,
    IngestRuntimeConfigVersion,
    IngestRuntimeJob,
    IngestRuntimeNode,
)
from whale.shared.persistence.orm.organization import Organization
from whale.shared.persistence.orm.scada_ingest import (
    CDCDict,
    CommunicationEndpoint,
    FCDict,
    IED,
    LDInstance,
    ScadaDataType,
    SignalProfile,
    SignalProfileItem,
)
from whale.shared.persistence.orm.model_asset import (
    ModelAsset,
    SimulationArtifact,
    SimulationCase,
    SimulationResult,
)
from whale.shared.persistence.orm.scada_protocol_param import (
    ScadaEndpointParamValue,
    ScadaProtocolParamDef,
    ScadaSignalParamDef,
    ScadaSignalProfileItemParamValue,
)

__all__ = [
    "Organization",
    "AssetType", "AssetModel", "AssetAttribute",
    "AssetInstance", "AssetBOM", "AssetRelation",
    "TopologyGraph", "TopologyNode", "TopologyEdge",
    "IED", "CommunicationEndpoint", "LDInstance",
    "SignalProfile", "SignalProfileItem",
    "ScadaDataType", "CDCDict", "FCDict",
    "AcqSignalState", "AcqSignalSample",
    "AcquisitionTask",
    "IngestSourceHealthOrm", "IngestRuntimeEventOrm",
    "IngestRuntimeNode", "IngestRuntimeJob", "IngestJobAssignment",
    "IngestJobLease", "IngestFencingToken", "IngestBundleMetadata",
    "IngestAuditEventOrm", "IngestRuntimeConfigVersion",
    "ModelAsset", "SimulationCase", "SimulationResult", "SimulationArtifact",
    "ScadaProtocolParamDef", "ScadaEndpointParamValue",
    "ScadaSignalParamDef", "ScadaSignalProfileItemParamValue",
]
