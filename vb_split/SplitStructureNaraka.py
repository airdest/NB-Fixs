"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


class Element:
    semantic_name = None
    semantic_index = None
    format = None
    input_slot = None
    aligned_byte_offset = None
    input_slot_class = None
    instance_data_step_rate = None

    # the order of the element,start from 0.
    element_number = None

    # the byte length of this Element's data.
    byte_width = None

    def revise(self):
        if self.semantic_name == b"POSITION":
            self.byte_width = 12
        if self.semantic_name == b"NORMAL":
            self.byte_width = 12
        if self.semantic_name == b"TANGENT":
            self.byte_width = 16
        if self.semantic_name == b"COLOR":
            self.byte_width = 4
        if self.semantic_name == b"TEXCOORD":
            if self.semantic_index == b"0":
                self.byte_width = 8
            else:
                self.byte_width = 8
                # TODO 测试它的原始R8G8B8A8_UNORM 是否能正确导入
                # element.format = b"R32G32B32A32_FLOAT"
        if self.semantic_name == b"BLENDWEIGHTS":
            self.byte_width = 16
        if self.semantic_name == b"BLENDINDICES":
            self.byte_width = 16


class HeaderInfo:
    file_index = None
    stride = None
    first_vertex = None
    vertex_count = None
    topology = None

    # Header have many semantic element,like POSITION,NORMAL,COLOR etc.
    elementlist = None

