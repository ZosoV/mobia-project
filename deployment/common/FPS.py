################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import time
import logging
start_time=time.time()
frame_count=0

class GETFPS:
    def __init__(self,stream_id):
        global start_time
        self.start_time=start_time
        self.is_first=True
        global frame_count
        self.frame_count=frame_count
        self.stream_id=stream_id
        self.current_fps = 0

    def get_fps(self, avg_seconds = 5):
        # average every x seconds
        end_time=time.time()
        if(self.is_first):
            self.start_time=end_time
            self.is_first=False
        if(end_time - self.start_time > avg_seconds):
            self.current_fps = float(self.frame_count)/ (end_time-self.start_time)
            logging.info("[FPS]: stream {} = {:.2f}".format(self.stream_id, self.current_fps))
            self.frame_count=0
            self.start_time=end_time
        else:
            self.frame_count=self.frame_count+1
        return self.current_fps

    def get_fps_per_frame(self):
        # every frame
        end_time=time.time()
        elapsed_time = end_time - self.start_time
        current_fps = 1.0/float(elapsed_time)
        self.start_time=end_time
        return current_fps

    def print_data(self):
        print('frame_count=',self.frame_count)
        print('start_time=',self.start_time)

