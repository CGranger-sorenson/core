// Copyright 2019-2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
//  * Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
//  * Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
//  * Neither the name of NVIDIA CORPORATION nor the names of its
//    contributors may be used to endorse or promote products derived
//    from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
// PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
// CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
// EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
// PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
// OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include "ensemble_model.h"

#include <stdint.h>

#include "constants.h"
#include "ensemble_scheduler.h"
#include "model_config_utils.h"
#include "triton/common/logging.h"

namespace triton { namespace core {

Status
EnsembleModel::Create(
    InferenceServer* server, const std::string& path,
    const ModelIdentifier& model_id, const int64_t version,
    const inference::ModelConfig& model_config, const bool is_config_provided,
    const double min_compute_capability, std::unique_ptr<Model>* model)
{
  // Create the ensemble model.
  std::unique_ptr<EnsembleModel> local_model(new EnsembleModel(
      min_compute_capability, path, model_id, version, model_config));

  RETURN_IF_ERROR(local_model->Init(is_config_provided));

  std::unique_ptr<Scheduler> scheduler;
  RETURN_IF_ERROR(EnsembleScheduler::Create(
      local_model->MutableStatsAggregator(), server, local_model->ModelId(),
      model_config, &scheduler));
  RETURN_IF_ERROR(local_model->SetScheduler(std::move(scheduler)));

  LOG_VERBOSE(1) << "ensemble model for " << local_model->Name() << std::endl;

  *model = std::move(local_model);
  return Status::Success;
}

std::ostream&
operator<<(std::ostream& out, const EnsembleModel& pb)
{
  out << "name=" << pb.Name() << std::endl;
  return out;
}

}}  // namespace triton::core
